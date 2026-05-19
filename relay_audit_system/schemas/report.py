"""
Pydantic v2 schemas for industrial relay feeder testing report extraction.

Supports motor feeder, transformer feeder, and bus coupler reports with
numerical and electromechanical relay configurations. Designed for LLM or
OCR extraction pipelines where field presence varies by site and template.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Shared primitives
# ---------------------------------------------------------------------------


class ExtractionModel(BaseModel):
    """Base model: optional fields, strip strings, ignore unknown keys at parse time."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class FeederType(StrEnum):
    """Primary feeder classification on the test report."""

    MOTOR = "motor"
    TRANSFORMER = "transformer"
    BUS_COUPLER = "bus_coupler"
    OTHER = "other"


class RelayTechnology(StrEnum):
    """Relay implementation family."""

    NUMERICAL = "numerical"
    ELECTROMECHANICAL = "electromechanical"
    HYBRID = "hybrid"
    OTHER = "other"


class PassFailStatus(StrEnum):
    """Normalized pass/fail/na outcome from site checks."""

    PASS = "pass"
    FAIL = "fail"
    NA = "na"
    PENDING = "pending"


class SettingEntry(ExtractionModel):
    """Single name/value setting row (relay pickup, time dial, plug, etc.)."""

    name: str | None = Field(default=None, description="Setting identifier or label from the report.")
    value: str | float | int | bool | None = Field(
        default=None,
        description="Parsed setting value; keep as string when units or ranges are ambiguous.",
    )
    unit: str | None = Field(default=None, description="Physical unit, e.g. A, s, %, V.")
    raw_text: str | None = Field(default=None, description="Verbatim text from the source document.")


class TestPoint(ExtractionModel):
    """One injected or simulated test point for a protection element or measurement."""

    label: str | None = Field(default=None, description="Row or step label, e.g. '2x pickup', 'Phase R'.")
    parameter: str | None = Field(
        default=None,
        description="Quantity under test, e.g. current, voltage, frequency, trip time.",
    )
    applied_value: str | float | int | None = Field(default=None, description="Injected or applied test value.")
    expected_value: str | float | int | None = Field(default=None, description="Expected outcome from settings.")
    measured_value: str | float | int | None = Field(default=None, description="Observed outcome.")
    unit: str | None = Field(default=None, description="Unit for applied/expected/measured values.")
    tolerance: str | None = Field(default=None, description="Allowed deviation, e.g. '±5%' or '0.2 s'.")
    result: PassFailStatus | str | None = Field(default=None, description="Pass/fail or site-specific result text.")
    remarks: str | None = Field(default=None, description="Per-point notes.")


class NameplateData(ExtractionModel):
    """Generic nameplate block reused across primary plant items."""

    manufacturer: str | None = None
    type_or_model: str | None = Field(default=None, alias="model")
    serial_number: str | None = None
    rated_voltage_kv: str | float | None = None
    rated_current_a: str | float | None = None
    rated_power_mva: str | float | None = None
    rated_power_mw: str | float | None = None
    year_of_manufacture: str | int | None = None
    additional_fields: list[SettingEntry] = Field(
        default_factory=list,
        description="Extra nameplate rows not covered by standard columns.",
    )


class ChecklistItem(ExtractionModel):
    """Reusable checklist row for final checks and functional tests."""

    item: str | None = Field(default=None, description="Check description or checklist ID.")
    result: PassFailStatus | str | None = None
    measured_value: str | float | int | None = None
    expected_value: str | float | int | None = None
    unit: str | None = None
    remarks: str | None = None


# ---------------------------------------------------------------------------
# Protection tests (flexible, not hardcoded per ANSI/IEC code)
# ---------------------------------------------------------------------------


class ProtectionTest(ExtractionModel):
    """
    Flexible protection test block.

    Use ``category`` for functional grouping (e.g. 'overcurrent', 'differential')
    and ``protection_code`` for element codes (e.g. '50', '51', '49', '46', 'DTOC').
    """

    category: str | None = Field(
        default=None,
        description="Functional group, e.g. overcurrent, earth fault, differential, sync.",
    )
    protection_code: str | None = Field(
        default=None,
        description="Element or scheme code from the report, e.g. 50/51, 49, 46, DTOC, REF.",
    )
    relay_label: str | None = Field(
        default=None,
        description="Relay or cubicle reference tied to this test, e.g. 'Main O/C', 'BB Diff'.",
    )
    description: str | None = Field(default=None, description="Free-text test title or scope.")
    settings: list[SettingEntry] = Field(
        default_factory=list,
        description="Pickup, time dial, curve, plug, CT ratio, and other settings for this element.",
    )
    test_points: list[TestPoint] = Field(
        default_factory=list,
        description="Injection steps, trip times, pickup multiples, or phase-wise results.",
    )
    overall_result: PassFailStatus | str | None = Field(
        default=None,
        description="Aggregate result for this protection test when reported once.",
    )
    remarks: str | None = None
    metadata: list[SettingEntry] = Field(
        default_factory=list,
        description="Template-specific keys not modeled elsewhere (curve type, zone, etc.).",
    )


# ---------------------------------------------------------------------------
# Document & extraction metadata
# ---------------------------------------------------------------------------


class DocumentMetadata(ExtractionModel):
    """Header and administrative fields from the test report cover sheet."""

    report_title: str | None = None
    report_number: str | None = None
    report_date: date | str | None = None
    site_name: str | None = None
    plant_or_substation: str | None = None
    bay_or_panel: str | None = None
    equipment_tag: str | None = None
    client_name: str | None = None
    contractor_name: str | None = None
    tested_by: str | None = None
    approved_by: str | None = None
    test_standard: str | None = Field(
        default=None,
        description="Referenced standard, e.g. IEC 60255, site procedure ID.",
    )
    revision: str | None = None
    language: str | None = None


class ExtractionMetadata(ExtractionModel):
    """Provenance and quality signals from the extraction pipeline."""

    source_file: str | None = None
    source_page_count: int | None = None
    extracted_at: datetime | str | None = None
    extractor_version: str | None = None
    model_name: str | None = None
    confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    field_confidence: list[SettingEntry] = Field(
        default_factory=list,
        description="Per-field or per-section confidence scores (name=field, value=score).",
    )
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    raw_blocks: list[str] = Field(
        default_factory=list,
        description="Unstructured snippets retained for human review.",
    )


# ---------------------------------------------------------------------------
# Feeder (motor / transformer / bus coupler)
# ---------------------------------------------------------------------------


class MotorFeederDetails(ExtractionModel):
    """Motor-specific feeder attributes when ``feeder_type`` is motor."""

    motor_tag: str | None = None
    rated_kw: str | float | None = None
    rated_rpm: str | float | None = None
    starting_method: str | None = Field(
        default=None,
        description="e.g. DOL, star-delta, VFD, soft starter.",
    )
    locked_rotor_current_a: str | float | None = None
    full_load_current_a: str | float | None = None


class TransformerFeederDetails(ExtractionModel):
    """Transformer-specific feeder attributes when ``feeder_type`` is transformer."""

    transformer_tag: str | None = None
    vector_group: str | None = None
    impedance_percent: str | float | None = None
    primary_voltage_kv: str | float | None = None
    secondary_voltage_kv: str | float | None = None
    tap_position: str | int | None = None
    cooling_type: str | None = None


class BusCouplerDetails(ExtractionModel):
    """Bus coupler / bus section attributes when ``feeder_type`` is bus_coupler."""

    coupler_name: str | None = None
    bus_a_name: str | None = None
    bus_b_name: str | None = None
    interlocking_scheme: str | None = None
    sync_check_required: bool | None = None
    auto_transfer_scheme: str | None = None


class Feeder(ExtractionModel):
    """Feeder identity, ratings, and type-specific extensions."""

    feeder_type: FeederType | str | None = Field(
        default=None,
        description="motor, transformer, bus_coupler, or site-specific label.",
    )
    feeder_name: str | None = None
    feeder_tag: str | None = None
    voltage_level: str | None = Field(default=None, description="e.g. 11 kV, 33 kV, 415 V.")
    rated_current_a: str | float | None = None
    rated_power: str | float | None = None
    power_unit: str | None = Field(default=None, description="MVA, MW, kW as stated on report.")
    ct_ratio: str | None = Field(default=None, description="Overall feeder CT ratio if given once.")
    vt_ratio: str | None = None
    nameplate: NameplateData | None = None
    motor_details: MotorFeederDetails | None = None
    transformer_details: TransformerFeederDetails | None = None
    bus_coupler_details: BusCouplerDetails | None = None
    remarks: str | None = None


# ---------------------------------------------------------------------------
# Primary plant: CB, CT, isolator, reactor, vacuum contactor
# ---------------------------------------------------------------------------


class CircuitBreaker(ExtractionModel):
    """HV/MV circuit breaker details and tests."""

    tag: str | None = None
    nameplate: NameplateData | None = None
    breaker_type: str | None = Field(default=None, description="e.g. SF6, vacuum, oil.")
    rated_voltage_kv: str | float | None = None
    rated_current_a: str | float | None = None
    breaking_capacity_ka: str | float | None = None
    operating_mechanism: str | None = None
    control_voltage_v: str | float | None = None
    close_coil_test: ChecklistItem | None = None
    trip_coil_test: ChecklistItem | None = None
    insulation_resistance_mohm: str | float | None = None
    contact_resistance_µohm: str | float | None = None
    timing_tests: list[TestPoint] = Field(
        default_factory=list,
        description="Open/close, pole discrepancy, or slow-close timing rows.",
    )
    functional_checks: list[ChecklistItem] = Field(default_factory=list)
    remarks: str | None = None


class CurrentTransformer(ExtractionModel):
    """Single CT set (phase-wise or multi-winding)."""

    tag: str | None = None
    location: str | None = Field(default=None, description="e.g. line, bus, neutral, REF.")
    phase: str | None = Field(default=None, description="R, Y, B, N, or combined.")
    ratio: str | None = Field(default=None, description="e.g. 400/1 A.")
    accuracy_class: str | None = None
    knee_point_voltage_v: str | float | None = None
    burden_va: str | float | None = None
    polarity_verified: PassFailStatus | str | None = None
    insulation_test_mohm: str | float | None = None
    ratio_test: list[TestPoint] = Field(default_factory=list)
    excitation_test: list[TestPoint] = Field(default_factory=list)
    remarks: str | None = None


class Isolator(ExtractionModel):
    """Disconnector / isolator section."""

    tag: str | None = None
    nameplate: NameplateData | None = None
    rated_voltage_kv: str | float | None = None
    rated_current_a: str | float | None = None
    contact_resistance: list[TestPoint] = Field(default_factory=list)
    operational_checks: list[ChecklistItem] = Field(default_factory=list)
    remarks: str | None = None


class Reactor(ExtractionModel):
    """Series or shunt reactor where present on the feeder."""

    tag: str | None = None
    nameplate: NameplateData | None = None
    rated_mvar: str | float | None = None
    rated_current_a: str | float | None = None
    insulation_test: list[TestPoint] = Field(default_factory=list)
    remarks: str | None = None


class VacuumContactor(ExtractionModel):
    """Vacuum contactor / VCB at LV or auxiliary duty."""

    tag: str | None = None
    nameplate: NameplateData | None = None
    rated_voltage_v: str | float | None = None
    rated_current_a: str | float | None = None
    control_voltage_v: str | float | None = None
    coil_tests: list[ChecklistItem] = Field(default_factory=list)
    contact_resistance: list[TestPoint] = Field(default_factory=list)
    timing_tests: list[TestPoint] = Field(default_factory=list)
    remarks: str | None = None


# ---------------------------------------------------------------------------
# Relay (numerical & electromechanical)
# ---------------------------------------------------------------------------


class NumericalRelayDetails(ExtractionModel):
    """Settings and identity fields typical of microprocessor relays."""

    firmware_version: str | None = None
    configuration_version: str | None = None
    communication_protocol: str | None = Field(default=None, description="e.g. IEC 61850, Modbus.")
    setting_group_active: str | int | None = None
    setting_file_reference: str | None = None
    event_counter_read: str | int | None = None
    self_test_result: PassFailStatus | str | None = None


class ElectromechanicalRelayDetails(ExtractionModel):
    """Plug, coil, and mechanical attributes for static/induction relays."""

    plug_setting_range: str | None = None
    time_dial_range: str | None = None
    coil_rating_v: str | float | None = None
    target_reset: PassFailStatus | str | None = None
    mechanical_alignment_check: PassFailStatus | str | None = None


class Relay(ExtractionModel):
    """
    One relay device on the feeder.

    A report may list main, backup, check, or bus differential relays; model each
    as a separate ``Relay`` entry in ``RelayFeederTestReport.relays``.
    """

    tag: str | None = None
    cubicle_or_panel: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    relay_technology: RelayTechnology | str | None = None
    relay_function: str | None = Field(
        default=None,
        description="e.g. feeder protection, BB differential, standby earth fault.",
    )
    rated_voltage_v: str | float | None = None
    ct_ratio_used: str | None = None
    vt_ratio_used: str | None = None
    numerical_details: NumericalRelayDetails | None = None
    electromechanical_details: ElectromechanicalRelayDetails | None = None
    installed_elements: list[str] = Field(
        default_factory=list,
        description="Declared protection codes configured in this relay, e.g. ['50', '51', '49'].",
    )
    remarks: str | None = None


class RelayMeasurement(ExtractionModel):
    """Measured quantities from relay display, SCADA, or test set readback."""

    relay_label: str | None = Field(default=None, description="Associates reading to a relay tag or role.")
    parameter: str | None = Field(default=None, description="e.g. Ia, Ib, Ic, Vn, frequency, power.")
    phase: str | None = None
    value: str | float | int | None = None
    unit: str | None = None
    measurement_time: str | None = None
    source: str | None = Field(default=None, description="e.g. relay LCD, clamp meter, injection set.")
    remarks: str | None = None


# ---------------------------------------------------------------------------
# Transformer-specific tests (oil, winding, protection related)
# ---------------------------------------------------------------------------


class TransformerTest(ExtractionModel):
    """Transformer or winding tests often bundled on transformer feeder reports."""

    test_name: str | None = Field(default=None, description="e.g. IR, Tan Delta, DGA, ratio, vector group.")
    category: str | None = Field(default=None, description="electrical, oil, mechanical, protection.")
    test_points: list[TestPoint] = Field(default_factory=list)
    settings: list[SettingEntry] = Field(default_factory=list)
    overall_result: PassFailStatus | str | None = None
    remarks: str | None = None


# ---------------------------------------------------------------------------
# LT breaker & earth fault LT relay
# ---------------------------------------------------------------------------


class LTBreaker(ExtractionModel):
    """Low-tension breaker or incomer on the feeder panel."""

    tag: str | None = None
    nameplate: NameplateData | None = None
    rated_current_a: str | float | None = None
    rated_voltage_v: str | float | None = None
    breaker_type: str | None = Field(default=None, description="e.g. MCCB, ACB, MCB.")
    trip_unit_model: str | None = None
    long_time_pickup_a: str | float | None = None
    short_time_pickup_a: str | float | None = None
    instantaneous_pickup_a: str | float | None = None
    ground_fault_pickup_a: str | float | None = None
    trip_tests: list[ProtectionTest] = Field(
        default_factory=list,
        description="LT trip verification using the same flexible protection structure.",
    )
    insulation_test_mohm: str | float | None = None
    contact_resistance: list[TestPoint] = Field(default_factory=list)
    operational_checks: list[ChecklistItem] = Field(default_factory=list)
    remarks: str | None = None


class EarthFaultLTRelay(ExtractionModel):
    """Dedicated earth-fault or standby earth-fault relay at LT."""

    tag: str | None = None
    relay_technology: RelayTechnology | str | None = None
    nameplate: NameplateData | None = None
    ct_ratio: str | None = None
    neutral_ct_ratio: str | None = None
    settings: list[SettingEntry] = Field(default_factory=list)
    protection_tests: list[ProtectionTest] = Field(default_factory=list)
    remarks: str | None = None


# ---------------------------------------------------------------------------
# Final checks & remarks
# ---------------------------------------------------------------------------


class FinalChecks(ExtractionModel):
    """Sign-off, interlocks, alarms, and commissioning checklist."""

    overall_result: PassFailStatus | str | None = None
    checklist: list[ChecklistItem] = Field(default_factory=list)
    interlocks_verified: list[ChecklistItem] = Field(default_factory=list)
    alarms_verified: list[ChecklistItem] = Field(default_factory=list)
    labels_and_placards_ok: PassFailStatus | str | None = None
    tested_by: str | None = None
    tested_date: date | str | None = None
    witnessed_by: str | None = None
    witnessed_date: date | str | None = None
    remarks: str | None = None


class Remarks(ExtractionModel):
    """Structured or free-form remarks sections."""

    general: str | None = None
    deficiencies: str | None = None
    recommendations: str | None = None
    safety_notes: str | None = None
    additional_sections: list[SettingEntry] = Field(
        default_factory=list,
        description="Titled remark blocks, e.g. {'name': 'Client comments', 'value': '...'}.",
    )


# ---------------------------------------------------------------------------
# Root report model
# ---------------------------------------------------------------------------


class RelayFeederTestReport(ExtractionModel):
    """
    Root schema for a single industrial relay feeder testing report.

    All top-level sections are optional to tolerate partial extraction. Repeated
    equipment (CTs, relays, protection elements) use lists.
    """

    document_metadata: DocumentMetadata | None = None
    feeder: Feeder | None = None
    circuit_breaker: CircuitBreaker | None = None
    current_transformers: list[CurrentTransformer] = Field(default_factory=list)
    relays: list[Relay] = Field(
        default_factory=list,
        description="All relays on the feeder including main, check, and specialized.",
    )
    relay_measurements: list[RelayMeasurement] = Field(default_factory=list)
    protection_tests: list[ProtectionTest] = Field(
        default_factory=list,
        description="Flexible protection test blocks; not limited to specific ANSI codes.",
    )
    transformer_tests: list[TransformerTest] = Field(
        default_factory=list,
        description="Populate for transformer feeders; may be empty for motor or bus coupler.",
    )
    lt_breaker: LTBreaker | None = None
    earth_fault_lt_relay: EarthFaultLTRelay | None = None
    isolator: Isolator | None = None
    reactor: Reactor | None = None
    vacuum_contactor: VacuumContactor | None = None
    final_checks: FinalChecks | None = None
    remarks: Remarks | str | None = Field(
        default=None,
        description="Structured remarks object or a single free-text block.",
    )
    extraction_metadata: ExtractionMetadata | None = None
