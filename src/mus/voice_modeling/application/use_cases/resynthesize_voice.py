"""Use case for resynthesizing a ParametricVoice into an AudioSignal."""

from dataclasses import dataclass
from pathlib import Path

from mus.shared_kernel.audio import AudioSignal
from mus.voice_modeling.application.ports import AudioWriterPort, VocoderPort
from mus.voice_modeling.domain.parametric_voice import ParametricVoice


@dataclass(frozen=True, slots=True)
class ResynthesizeVoiceCommand:
    """Input command to resynthesize voice to an AudioSignal and optional output file."""

    voice: ParametricVoice
    output_path: Path | None = None


class ResynthesizeVoice:
    """Use case coordinating vocoder synthesis and optional audio export."""

    def __init__(
        self,
        vocoder: VocoderPort,
        writer: AudioWriterPort | None = None,
    ) -> None:
        self._vocoder = vocoder
        self._writer = writer

    def execute(self, command: ResynthesizeVoiceCommand) -> AudioSignal:
        """Synthesizes the voice aggregate and writes to disk if output_path is set."""
        signal = self._vocoder.synthesize(command.voice)

        if self._writer and command.output_path:
            self._writer.write(signal, command.output_path)

        return signal
