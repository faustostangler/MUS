import pytest
from validate_emblem import parse_spec_code, EmblemSpec

def test_medical_bionic_eye_spec():
    # Spec code for the medical bionic eye emblem
    spec_code = "G-NONE-B-01-D-NONE-T-Solid-F-None-P-Hybrid3-H150S60L15H45S80L55H0S0L100-I-BionicEye-PolicyB"
    parsed = parse_spec_code(spec_code)
    assert parsed.geometry_code == "G-NONE"
    assert parsed.boundary_code == "B-01"
    assert parsed.field_division_code == "D-NONE"
    assert parsed.texture_code == "Solid"
    assert parsed.frame_code == "None"
    assert parsed.palette_type == "Hybrid3"
    assert len(parsed.colors) == 3
    assert parsed.colors[0].hue == 150.0
    assert parsed.colors[0].saturation == 60.0
    assert parsed.colors[0].lightness == 15.0 # Deep Green
    assert parsed.colors[1].hue == 45.0
    assert parsed.colors[1].saturation == 80.0
    assert parsed.colors[1].lightness == 55.0 # Gold
    assert parsed.colors[2].hue == 0.0
    assert parsed.colors[2].saturation == 0.0
    assert parsed.colors[2].lightness == 100.0 # White
    assert parsed.charge_code == "BionicEye"
    assert parsed.lod3_policy == "PolicyB"

def test_rule_of_tincture_violation():
    # If the lightness difference between deep green and gold is less than 40%, it should fail
    invalid_spec = "G-NONE-B-01-D-NONE-T-Solid-F-None-P-Hybrid3-H150S60L25H45S80L55H0S0L100-I-BionicEye-PolicyB"
    with pytest.raises(Exception):
        parse_spec_code(invalid_spec)

def test_medical_flag_spec():
    # Spec code for the vertical flag geometry (G-CF-01) with BionicCross charge
    spec_code = "G-CF-01-B-01-D-NONE-T-Solid-F-None-P-Hybrid3-H150S60L15H0S0L100H45S80L55-I-BionicCross-PolicyB"
    parsed = parse_spec_code(spec_code)
    assert parsed.geometry_code == "G-CF-01"
    assert parsed.boundary_code == "B-01"
    assert parsed.field_division_code == "D-NONE"
    assert parsed.texture_code == "Solid"
    assert parsed.frame_code == "None"
    assert parsed.palette_type == "Hybrid3"
    assert len(parsed.colors) == 3
    assert parsed.colors[0].hue == 150.0 # Green
    assert parsed.colors[1].hue == 0.0   # White
    assert parsed.colors[2].hue == 45.0  # Gold
    assert parsed.charge_code == "BionicCross"
    assert parsed.lod3_policy == "PolicyB"
