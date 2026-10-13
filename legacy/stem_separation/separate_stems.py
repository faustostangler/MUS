#!/usr/bin/env python3
"""Demucs Stem Extraction (Meta AI) with Ollama AI Tagging and YouTube Playlist Downloader (yt-dlp).

TWO-PHASE BATCH PIPELINE WITH HISTORY CONTROL:
  - history.json: Banco de controle local de faixas já concluídas (elimina retrabalho).
  - LOTE 1 (LLM/Ollama): Faz o tagging e download de todas as faixas pendentes mantendo o Ollama aquecido.
  - TRANSIÇÃO: Descarrega o Ollama da VRAM uma única vez e limpa a GPU.
  - LOTE 2 (Demucs SOTA): A GPU fica 100% livre para o Demucs processar os 6 stems em lote no modo MÁXIMO.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from typing import Any, cast
import urllib.request

# Evita fragmentação de memória VRAM no PyTorch (CUDA)
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import torch
import yt_dlp
import demucs.apply
from demucs.separate import main as demucs_main
import tqdm

# Ajuste visual da barra de progresso do Demucs para caber no terminal sem quebrar linha
_orig_tqdm = demucs.apply.tqdm.tqdm


def _compact_tqdm(*args: Any, **kwargs: Any) -> Any:
    # Reduz de ncols=120 (muito largo) para 50 colunas para evitar estouro de linha no console
    kwargs["ncols"] = min(kwargs.get("ncols", 50), 50)
    return _orig_tqdm(*args, **kwargs)


setattr(demucs.apply.tqdm, "tqdm", _compact_tqdm)

# ==============================================================================
# CONFIGURAÇÃO DE QUALIDADE (DEMUCS / META AI)
# ==============================================================================
DEFAULT_MODEL = "htdemucs_6s"    # Modelo de 6 Stems (Vocals, Drums, Bass, Other, Guitar, Piano)
DEFAULT_SHIFTS = 5               # 5 passagens de estabilização equivariante (elimina artefatos)
DEFAULT_OVERLAP = 0.50           # 50% de sobreposição para junção perfeita dos chunks
DEFAULT_MP3_BITRATE = 320        # 320 kbps (qualidade máxima de MP3)
DEFAULT_MP3_PRESET = 2           # Preset 2 do encoder LAME (máxima fidelidade acústica)
DEFAULT_CLIP_MODE = "rescale"    # Evita qualquer distorção digital reescalando picos > 0dBFS

STEMS_6S = ["vocals", "drums", "bass", "other", "guitar", "piano"]
STEMS_4S = ["vocals", "drums", "bass", "other"]

# ADR-001 D8: legacy script reads the shared data root via env (12-Factor); defaults to repo data/.
_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DEFAULT_PLAYLIST_FILE = Path(os.environ.get("MUS_PLAYLIST_FILE", _DATA_DIR / "playlist.txt"))
DEFAULT_LIBRARY_DIR = Path(os.environ.get("MUS_LIBRARY_DIR", _DATA_DIR / "library"))
DEFAULT_HISTORY_FILE = Path(os.environ.get("MUS_HISTORY_FILE", _DATA_DIR / "history.json"))
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
OLLAMA_HOST = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:latest"


# ==============================================================================
# CONTROLE DE HISTÓRICO (BANCO LOCAL DE FAIXAS CONCLUÍDAS)
# ==============================================================================
def load_history(history_file: Path = DEFAULT_HISTORY_FILE) -> dict[str, Any]:
    """Carrega o histórico de faixas processadas do arquivo JSON."""
    if not history_file.exists():
        return {"tracks": {}}
    try:
        with open(history_file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "tracks" in data:
                return data
            return {"tracks": {}}
    except Exception as e:
        print(f"[Histórico] Aviso ao ler histórico ({e}). Criando nova base.")
        return {"tracks": {}}


def save_history(history: dict[str, Any], history_file: Path = DEFAULT_HISTORY_FILE) -> None:
    """Salva o histórico atualizado em disco de forma segura."""
    tmp_file = history_file.with_suffix(".tmp")
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        tmp_file.replace(history_file)
    except Exception as e:
        print(f"[Histórico] Erro ao salvar histórico: {e}")


def is_track_completed(
    history: dict[str, Any],
    video_id: str,
    library_dir: Path,
    expected_stems: list[str] = STEMS_6S,
) -> bool:
    """Verifica se a faixa já foi registrada e se todos os stems estão de fato no disco."""
    tracks = history.get("tracks", {})
    if video_id in tracks:
        entry = tracks[video_id]
        audio_rel = entry.get("audio_file")
        if audio_rel:
            audio_path = library_dir / audio_rel
            if audio_path.exists() and stems_already_exist(audio_path, stems=expected_stems):
                return True
    return False


def record_history_entry(
    history: dict[str, Any],
    video_id: str,
    title: str,
    artist: str,
    track: str,
    genre: str,
    audio_file: Path,
    stems: list[Path],
    library_dir: Path,
    history_file: Path = DEFAULT_HISTORY_FILE,
) -> None:
    """Registra uma faixa concluída com seus metadados e arquivos."""
    tracks = history.setdefault("tracks", {})
    try:
        rel_audio = str(audio_file.relative_to(library_dir))
    except ValueError:
        rel_audio = str(audio_file)

    tracks[video_id] = {
        "video_id": video_id,
        "title": title,
        "artist": artist,
        "track": track,
        "genre": genre,
        "audio_file": rel_audio,
        "stems": [s.name for s in sorted(stems)],
        "processed_at": datetime.datetime.now().isoformat(),
    }
    save_history(history, history_file)


# ==============================================================================
# OLLAMA & IA METADATA
# ==============================================================================
def sanitize_filename(name: str) -> str:
    """Remove caracteres inválidos para caminhos de arquivos e pastas."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return cleaned or "Unknown"


def unload_ollama_model(model: str = DEFAULT_OLLAMA_MODEL, host: str = OLLAMA_HOST) -> None:
    """Libera explicitamente o modelo Ollama da VRAM da GPU."""
    print(f"\n[GPU VRAM] Descarregando modelo '{model}' do Ollama da VRAM...")
    try:
        req = urllib.request.Request(
            f"{host}/api/generate",
            data=json.dumps({"model": model, "keep_alive": 0}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
        print("[GPU VRAM] Memória GPU do Ollama liberada com sucesso.")
    except Exception as e:
        print(f"[GPU VRAM] Aviso ao descarregar Ollama: {e}")


def query_ollama_metadata(
    title: str,
    channel: str,
    description: str,
    model: str = DEFAULT_OLLAMA_MODEL,
    host: str = OLLAMA_HOST,
) -> dict[str, str]:
    """Classifica gênero, artista e nome da faixa usando o modelo local do Ollama."""
    prompt = f"""Given the music video title, channel, and description, identify:
1. genre (broad musical genre like "Rock", "Samba-Reggae", "Pop", "Jazz", "Hip Hop", "Eletronica", "MPB", "Reggae", etc. - clean and suitable for folder naming)
2. artist (main artist or band name)
3. track (song title, without feat or extra noise)

Input:
Title: {title}
Channel/Uploader: {channel}
Description:
{description[:1500]}

Respond strictly in valid JSON with keys "genre", "artist", "track". Do not include markdown codeblocks or explanation.
"""
    result = {
        "genre": "Unknown",
        "artist": sanitize_filename(channel or "Unknown"),
        "track": sanitize_filename(title or "Track"),
    }

    for attempt in range(2):
        try:
            req = urllib.request.Request(
                f"{host}/api/generate",
                data=json.dumps({
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw_res = json.loads(resp.read().decode("utf-8"))
                data = json.loads(raw_res.get("response", "{}"))
                result["genre"] = sanitize_filename(data.get("genre") or "Unknown")
                result["artist"] = sanitize_filename(data.get("artist") or channel or "Unknown")
                result["track"] = sanitize_filename(data.get("track") or title or "Track")
                break
        except Exception as e:
            if attempt == 0:
                print(f"[Ollama] Tentativa 1 falhou ({e}). Tentando novamente...")
                continue
            print(f"[Ollama] Aviso: Não foi possível inferir metadados via LLM ({e}). Usando tags básicas.")
            break

    return result


def stems_already_exist(audio_path: Path, stems: list[str] = STEMS_6S) -> bool:
    """Verifica se todos os arquivos MP3 de stems esperados já existem na pasta."""
    target_dir = audio_path.parent
    base_stem_name = audio_path.stem
    return all((target_dir / f"{base_stem_name} - {s}.mp3").exists() for s in stems)


# ==============================================================================
# DOWNLOAD E EXTRAÇÃO DE METADADOS (YT-DLP)
# ==============================================================================
def get_js_runtime_config() -> dict[str, Any]:
    """Configura o runtime JavaScript (Node.js) para o yt-dlp resolver assinaturas e evitar HTTP 403."""
    node_bin = shutil.which("node")
    if not node_bin:
        nvm_dir = Path.home() / ".nvm" / "versions" / "node"
        if nvm_dir.exists():
            versions = sorted(nvm_dir.glob("*/bin/node"), reverse=True)
            if versions:
                node_bin = str(versions[0])
    
    if node_bin:
        return {"node": {"path": node_bin}}
    return {}


def extract_tracks_from_url(url: str) -> list[Any]:
    """Extrai todas as faixas de um link individual ou playlist do YouTube."""
    ydl_opts: dict[str, Any] = {
        "quiet": True,
        "extract_flat": "in_playlist",
        "noplaylist": False,
        "no_warnings": True,
    }
    js_runtimes = get_js_runtime_config()
    if js_runtimes:
        ydl_opts["js_runtimes"] = js_runtimes

    with yt_dlp.YoutubeDL(cast(Any, ydl_opts)) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"[yt-dlp] Erro ao extrair link {url}: {e}")
            return []

        if not info:
            return []

        entries = info.get("entries")
        if entries is not None:
            entry_list = [e for e in entries if e]
            print(f"[yt-dlp] Playlist detectada: '{info.get('title', 'Sem Título')}' com {len(entry_list)} faixa(s).")
            return list(entry_list)
        else:
            return [info]


def download_single_track(
    entry: dict[str, Any] | Any,
    library_dir: Path,
    expected_stems: list[str] = STEMS_6S,
    ollama_model: str = DEFAULT_OLLAMA_MODEL,
) -> tuple[Path, dict[str, str], bool]:
    """Etiqueta com Ollama e baixa áudio se necessário."""
    title = entry.get("title") or "Unknown Title"
    channel = entry.get("uploader") or entry.get("channel") or "Unknown Artist"
    description = entry.get("description") or ""

    video_url_candidate: str | None = entry.get("webpage_url") or entry.get("url")
    if not video_url_candidate and entry.get("id"):
        video_url_candidate = f"https://music.youtube.com/watch?v={entry.get('id')}"

    video_url: str = video_url_candidate or ""

    js_runtimes = get_js_runtime_config()

    if not description and video_url:
        try:
            probe_opts: dict[str, Any] = {"quiet": True, "no_warnings": True}
            if js_runtimes:
                probe_opts["js_runtimes"] = js_runtimes
            with yt_dlp.YoutubeDL(cast(Any, probe_opts)) as ydl:
                full_info = ydl.extract_info(video_url, download=False)
                if full_info:
                    title = full_info.get("title") or title
                    channel = full_info.get("uploader") or full_info.get("channel") or channel
                    description = full_info.get("description") or ""
        except Exception:
            pass

    print(f"\n[Fase 1: AI Tagging] Consultando Ollama ({ollama_model}): '{title}'...")
    metadata = query_ollama_metadata(
        title=title,
        channel=channel,
        description=description,
        model=ollama_model,
    )
    genre = metadata["genre"]
    artist = metadata["artist"]
    track = metadata["track"]

    print(f"[Fase 1: AI Tagging] Identificado -> Gênero: '{genre}' | Artista: '{artist}' | Música: '{track}'")

    file_stem = f"{artist} - {track}"
    
    # Verifica se já existe em qualquer subpasta de gênero na biblioteca
    existing_in_library = list(library_dir.glob(f"*/{file_stem}.mp3"))
    if existing_in_library:
        expected_mp3 = existing_in_library[0]
        genre_dir = expected_mp3.parent
        print(f"[Library] Áudio já presente em: {genre_dir.name}/{expected_mp3.name}")
    else:
        genre_dir = library_dir / genre
        genre_dir.mkdir(parents=True, exist_ok=True)
        expected_mp3 = genre_dir / f"{file_stem}.mp3"

    # Verifica se todos os stems já existem
    if stems_already_exist(expected_mp3, stems=expected_stems):
        print(f"[Cache] Todos os {len(expected_stems)} stems já existem para: '{file_stem}'.")
        return expected_mp3, metadata, True

    if expected_mp3.exists():
        return expected_mp3, metadata, False

    out_template = str(genre_dir / f"{file_stem}.%(ext)s")
    ydl_dl_opts: dict[str, Any] = {
        "format": "bestaudio/best",
        "outtmpl": out_template,
        "noplaylist": True,
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "buffersize": 1024 * 64,
        "http_chunk_size": 10485760,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
        "quiet": False,
        "no_warnings": True,
    }
    if js_runtimes:
        ydl_dl_opts["js_runtimes"] = js_runtimes

    if not video_url:
        raise ValueError(f"Could not determine video URL for entry: {title}")

    max_retries = 3
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[yt-dlp] Baixando áudio (tentativa {attempt}/{max_retries}): {title} -> {file_stem}.mp3")
            current_opts = dict(ydl_dl_opts)
            if attempt == 2:
                current_opts["format"] = "140/bestaudio/best"
            with yt_dlp.YoutubeDL(cast(Any, current_opts)) as ydl:
                ydl.download([video_url])
            if expected_mp3.exists():
                last_error = None
                break
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = attempt * 3
                print(f"[yt-dlp] Falha temporária na tentativa {attempt} ({e}). Tentando novamente em {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"[yt-dlp] Erro persistente após {max_retries} tentativas: {e}")

    if last_error is not None and not expected_mp3.exists():
        raise last_error

    assert expected_mp3.exists(), f"Downloaded audio not found at: {expected_mp3}"
    print(f"[yt-dlp] Salvo: {expected_mp3.name}")
    return expected_mp3, metadata, False


# ==============================================================================
# SEPARAÇÃO DE STEMS (DEMUCS SOTA)
# ==============================================================================
def separate_stems_in_place(
    audio_path: Path,
    model: str = DEFAULT_MODEL,
    device: str = DEFAULT_DEVICE,
    shifts: int = DEFAULT_SHIFTS,
    overlap: float = DEFAULT_OVERLAP,
    mp3_bitrate: int = DEFAULT_MP3_BITRATE,
    mp3_preset: int = DEFAULT_MP3_PRESET,
    clip_mode: str = DEFAULT_CLIP_MODE,
    two_stems: str | None = None,
) -> list[Path]:
    """Separa áudio nos stems salvos na mesma pasta como {artista} - {musica} - {stem}.mp3."""
    audio_path = Path(audio_path).resolve()
    assert audio_path.exists(), f"Arquivo de áudio não encontrado: {audio_path}"

    target_dir = audio_path.parent
    base_stem_name = audio_path.stem

    temp_demucs_dir = target_dir / ".tmp_demucs"
    temp_demucs_dir.mkdir(parents=True, exist_ok=True)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    # Argumentos com chunk segment de 4s otimizado para placas de 6GB
    cmd_args = [
        "-n", model,
        "-o", str(temp_demucs_dir),
        "-d", device,
        "--shifts", str(shifts),
        "--overlap", str(overlap),
        "--segment", "4",
        "--mp3",
        "--mp3-bitrate", str(mp3_bitrate),
        "--mp3-preset", str(mp3_preset),
        "--clip-mode", clip_mode,
    ]

    if two_stems:
        cmd_args.extend(["--two-stems", two_stems])

    cmd_args.append(str(audio_path))

    print(f"\n[Demucs] Separando stems para: {audio_path.name}")
    print(f"[Demucs] Config: Modelo={model} | Shifts={shifts} | Overlap={overlap*100:.0f}% | Segment=4s | MP3={mp3_bitrate}kbps | Device={device}")
    
    try:
        demucs_main(cmd_args)
    except Exception as err:
        if "out of memory" in str(err).lower() and device == "cuda":
            print("\n[Demucs] Aviso: GPU VRAM atingiu o limite com segment=4s. Tentando com segment=2s...")
            torch.cuda.empty_cache()
            seg_idx = cmd_args.index("--segment")
            cmd_args[seg_idx + 1] = "2"
            try:
                demucs_main(cmd_args)
            except Exception as err2:
                if "out of memory" in str(err2).lower():
                    print("\n[Demucs] Aviso: Fallback para CPU devido a restrições de VRAM...")
                    dev_idx = cmd_args.index("-d")
                    cmd_args[dev_idx + 1] = "cpu"
                    demucs_main(cmd_args)
                else:
                    raise err2
        else:
            raise err

    raw_output_folder = temp_demucs_dir / model / audio_path.stem
    generated_stems: list[Path] = []

    if raw_output_folder.exists():
        for stem_file in raw_output_folder.glob("*.mp3"):
            stem_type = stem_file.stem
            final_stem_path = target_dir / f"{base_stem_name} - {stem_type}.mp3"
            shutil.move(str(stem_file), str(final_stem_path))
            generated_stems.append(final_stem_path)

        shutil.rmtree(temp_demucs_dir, ignore_errors=True)

    return generated_stems


def read_playlist_file(playlist_path: Path) -> list[str]:
    """Lê URLs de um arquivo txt, ignorando linhas vazias e comentários."""
    if not playlist_path.exists():
        return []
    with open(playlist_path, encoding="utf-8") as f:
        lines = [line.strip() for line in f]
    return [line for line in lines if line and not line.startswith("#")]


# ==============================================================================
# MAIN
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download YouTube videos/playlists e separa em 6 Stems MAX com controle de histórico (history.json)."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=None,
        help="YouTube URL, playlist URL, arquivo de áudio local, ou arquivo txt com links (padrão: playlist.txt)",
    )
    parser.add_argument("-o", "--out", default=DEFAULT_LIBRARY_DIR, type=Path, help="Diretório raiz da biblioteca musical")
    parser.add_argument("--history", default=DEFAULT_HISTORY_FILE, type=Path, help="Arquivo JSON de histórico de faixas")
    
    # Presets de qualidade
    parser.add_argument(
        "--preset",
        choices=["max", "balanced", "fast"],
        default="max",
        help="Preset de qualidade: 'max' (htdemucs_6s, 5 shifts, 50%% overlap, 320kbps), 'balanced' (1 shift, 25%% overlap), 'fast' (0 shifts, 10%% overlap)",
    )
    parser.add_argument("-m", "--model", default=None, help=f"Modelo do Demucs (padrão: {DEFAULT_MODEL} [6 stems])")
    parser.add_argument("--shifts", type=int, default=None, help="Número de random shifts (0-10)")
    parser.add_argument("--overlap", type=float, default=None, help="Fração de overlap dos chunks (0.1 - 0.75)")
    parser.add_argument("-d", "--device", default=DEFAULT_DEVICE, help=f"Dispositivo de execução (padrão: {DEFAULT_DEVICE})")
    parser.add_argument("--two-stems", default=None, help="Isolar apenas um stem (ex: 'vocals') e o resto instrumental")
    parser.add_argument("--ollama-model", default=DEFAULT_OLLAMA_MODEL, help=f"Modelo Ollama para tagging (padrão: {DEFAULT_OLLAMA_MODEL})")

    args = parser.parse_args()

    # Aplicação de Presets (padrão absoluto: htdemucs_6s)
    default_active_model = args.model or DEFAULT_MODEL
    if args.preset == "max":
        model = default_active_model
        shifts = args.shifts if args.shifts is not None else 5
        overlap = args.overlap if args.overlap is not None else 0.50
        mp3_bitrate = 320
    elif args.preset == "balanced":
        model = default_active_model
        shifts = args.shifts if args.shifts is not None else 1
        overlap = args.overlap if args.overlap is not None else 0.25
        mp3_bitrate = 256
    else:  # fast
        model = default_active_model
        shifts = args.shifts if args.shifts is not None else 0
        overlap = args.overlap if args.overlap is not None else 0.10
        mp3_bitrate = 192

    expected_stems = STEMS_6S if "6s" in model else STEMS_4S

    # Carrega banco de histórico local
    history = load_history(args.history)

    urls_or_files: list[str] = []
    if args.target:
        target_path = Path(args.target)
        if target_path.exists() and target_path.is_file() and target_path.suffix == ".txt":
            urls_or_files = read_playlist_file(target_path)
        else:
            urls_or_files = [args.target]
    elif DEFAULT_PLAYLIST_FILE.exists():
        urls_or_files = read_playlist_file(DEFAULT_PLAYLIST_FILE)

    if not urls_or_files:
        print("Demucs 6-Stems & Ollama Music Library Extractor")
        print(f"Dispositivo: {DEFAULT_DEVICE} (CUDA: {torch.cuda.is_available()}) | Ollama: {args.ollama_model}")
        print(f"Preset Padrão: MAX (Modelo: {model} [6 STEMS], Shifts: {shifts}, Overlap: {overlap*100:.0f}%, Bitrate: {mp3_bitrate}k)")
        print(f"\nNenhum link especificado e {DEFAULT_PLAYLIST_FILE.name} está vazio.")
        print("\nComo usar:")
        print("  1. Adicione URLs ou Playlists ao playground/music/playlist.txt e execute:")
        print("     python playground/music/separate_stems.py")
        sys.exit(0)

    print("\n" + "=" * 70)
    print("INICIANDO PIPELINE EM DOIS LOTES COM CONTROLE DE HISTÓRICO")
    print(f"Total de linhas no playlist.txt: {len(urls_or_files)}")
    print(f"Histórico carregado: {len(history.get('tracks', {}))} faixa(s) registrada(s) em {args.history.name}")
    print(f"Preset Ativo: {args.preset.upper()} (Modelo={model} [6 STEMS], Shifts={shifts}, Overlap={overlap*100:.0f}%, MP3={mp3_bitrate}kbps)")
    print("=" * 70)

    # ==============================================================================
    # LOTE 1: INGESTÃO, AI TAGGING E DOWNLOADS (OLLAMA ATIVO NA GPU)
    # ==============================================================================
    print("\n>>> [LOTE 1/2] FASE DE INGESTÃO, TAGGING COM OLLAMA E DOWNLOADS <<<")
    print("Verificando histórico e baixando apenas faixas pendentes.\n")

    # Lista de tuplas: (audio_path, video_id, metadata)
    tracks_to_process: list[tuple[Path, str, dict[str, str]]] = []
    total_entries_count = 0
    skipped_history_count = 0

    for line_idx, raw_item in enumerate(urls_or_files, start=1):
        if raw_item.startswith("http://") or raw_item.startswith("https://"):
            track_entries = extract_tracks_from_url(raw_item)
            if not track_entries:
                print(f"[Aviso] Nenhuma faixa encontrada para: {raw_item}")
                continue

            total_entries_count += len(track_entries)
            for t_idx, entry in enumerate(track_entries, start=1):
                vid_id = entry.get("id") or entry.get("url") or f"track_{line_idx}_{t_idx}"
                track_title = entry.get("title") or "Unknown"

                # 1. Checagem direta no histórico (instantânea, sem rede nem LLM)
                if is_track_completed(history, vid_id, args.out, expected_stems=expected_stems):
                    print(f"[Histórico ✓] Faixa já concluída anteriormente: '{track_title}' (ID: {vid_id}). Pulando.")
                    skipped_history_count += 1
                    continue

                # 2. Se pendente, consulta Ollama e baixa áudio
                try:
                    audio_file, meta, had_stems = download_single_track(
                        entry=entry,
                        library_dir=args.out,
                        expected_stems=expected_stems,
                        ollama_model=args.ollama_model,
                    )
                except Exception as dl_err:
                    print(f"\n[Aviso] Falha ao baixar faixa '{track_title}' (ID: {vid_id}): {dl_err}")
                    print("[Aviso] Continuando com as demais faixas da lista...\n")
                    continue

                if had_stems:
                    # Registra no histórico se já tinha os stems
                    stems_found = list(audio_file.parent.glob(f"{audio_file.stem} - *.mp3"))
                    record_history_entry(
                        history=history,
                        video_id=vid_id,
                        title=track_title,
                        artist=meta["artist"],
                        track=meta["track"],
                        genre=meta["genre"],
                        audio_file=audio_file,
                        stems=stems_found,
                        library_dir=args.out,
                        history_file=args.history,
                    )
                    skipped_history_count += 1
                else:
                    tracks_to_process.append((audio_file, vid_id, meta))

                # Pequena pausa entre downloads para evitar throttling do YouTube
                time.sleep(1.0)

        else:
            local_path = Path(raw_item)
            assert local_path.exists(), f"Arquivo local não encontrado: {local_path}"
            total_entries_count += 1
            vid_id = local_path.stem
            if is_track_completed(history, vid_id, args.out, expected_stems=expected_stems) or stems_already_exist(local_path, stems=expected_stems):
                print(f"[Histórico ✓] Faixa local já possui todos os stems: '{local_path.name}'. Pulando.")
                skipped_history_count += 1
            else:
                meta = {"genre": local_path.parent.name, "artist": "Various", "track": local_path.stem}
                tracks_to_process.append((local_path, vid_id, meta))

    # ==============================================================================
    # TRANSIÇÃO DE LOTE: DESCARREGAR OLLAMA E LIBERAR VRAM TOTAL
    # ==============================================================================
    print("\n" + "=" * 70)
    print(f"FASE 1 CONCLUÍDA! Total de faixas avaliadas: {total_entries_count}")
    print(f"Faixas puladas pelo histórico/disco: {skipped_history_count}")
    print(f"Faixas pendentes para separação de stems: {len(tracks_to_process)}")
    print("=" * 70)

    if tracks_to_process:
        unload_ollama_model(model=args.ollama_model, host=OLLAMA_HOST)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    # ==============================================================================
    # LOTE 2: SEPARAÇÃO DE STEMS COM DEMUCS (GPU 100% DEDICADA)
    # ==============================================================================
    if not tracks_to_process:
        print("\n✓ Todas as faixas já estão concluídas e salvas no histórico!")
    else:
        print(f"\n>>> [LOTE 2/2] FASE DE SEPARAÇÃO COM DEMUCS ({len(tracks_to_process)} faixa(s)) <<<")
        print(f"GPU totalmente dedicada ao modelo {model} (6 Stems MAX).\n")

        for idx, (audio_file, vid_id, meta) in enumerate(tracks_to_process, start=1):
            print(f"\n--------------------------------------------------")
            print(f"[{idx}/{len(tracks_to_process)}] Processando Stems: {audio_file.name}")
            print(f"--------------------------------------------------")

            try:
                stems = separate_stems_in_place(
                    audio_path=audio_file,
                    model=model,
                    device=args.device,
                    shifts=shifts,
                    overlap=overlap,
                    mp3_bitrate=mp3_bitrate,
                    mp3_preset=DEFAULT_MP3_PRESET,
                    clip_mode=DEFAULT_CLIP_MODE,
                    two_stems=args.two_stems,
                )

                # Registra no histórico imediatamente após a conclusão da faixa
                record_history_entry(
                    history=history,
                    video_id=vid_id,
                    title=meta.get("track", audio_file.stem),
                    artist=meta.get("artist", "Unknown"),
                    track=meta.get("track", audio_file.stem),
                    genre=meta.get("genre", audio_file.parent.name),
                    audio_file=audio_file,
                    stems=stems,
                    library_dir=args.out,
                    history_file=args.history,
                )

                print(f"\n✓ 6 Stems salvos em: {audio_file.parent}")
                for stem_file in sorted(stems):
                    size_mb = stem_file.stat().st_size / (1024 * 1024)
                    print(f"  • {stem_file.name} ({size_mb:.2f} MB)")
                print(f"[Histórico] Faixa registrada no {args.history.name} com sucesso.")
            except Exception as demucs_err:
                print(f"\n[Aviso] Falha ao separar stems de '{audio_file.name}': {demucs_err}")
                print("[Aviso] Continuando com as demais faixas da fila...\n")

    print("\n" + "=" * 70)
    print("✓ PIPELINE COMPLETO EXECUTADO COM SUCESSO!")
    print("=" * 70)
