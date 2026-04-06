from pathlib import Path

from src.apple_health.database import AppleHealthDatabase
from src.apple_health.importer import AppleHealthImporter
from src.config import Config


APPLE_HEALTH_EXPORT = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_US">
  <ExportDate value="2026-04-05 10:00:00 -0700"/>
  <Me
    HKCharacteristicTypeIdentifierDateOfBirth="1990-01-01"
    HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale"
    HKCharacteristicTypeIdentifierBloodType="HKBloodTypeNotSet"
    HKCharacteristicTypeIdentifierFitzpatrickSkinType="HKFitzpatrickSkinTypeNotSet"
    HKCharacteristicTypeIdentifierCardioFitnessMedicationsUse="HKCardioFitnessMedicationsUseNone"
  />
  <Workout
    workoutActivityType="HKWorkoutActivityTypeRunning"
    duration="30"
    durationUnit="min"
    totalEnergyBurned="320"
    totalEnergyBurnedUnit="kcal"
    sourceName="Apple Watch"
    sourceVersion="10.0"
    device="Watch"
    creationDate="2026-04-01 07:31:00 -0700"
    startDate="2026-04-01 07:00:00 -0700"
    endDate="2026-04-01 07:30:00 -0700"
  >
    <WorkoutStatistics
      type="HKQuantityTypeIdentifierHeartRate"
      startDate="2026-04-01 07:00:00 -0700"
      endDate="2026-04-01 07:30:00 -0700"
      average="152"
      maximum="178"
      unit="count/min"
    />
    <WorkoutStatistics
      type="HKQuantityTypeIdentifierActiveEnergyBurned"
      startDate="2026-04-01 07:00:00 -0700"
      endDate="2026-04-01 07:30:00 -0700"
      sum="300"
      unit="kcal"
    />
  </Workout>
  <Workout
    workoutActivityType="HKWorkoutActivityTypeWalking"
    duration="20"
    durationUnit="min"
    sourceName="Apple Watch"
    creationDate="2026-04-02 18:21:00 -0700"
    startDate="2026-04-02 18:00:00 -0700"
    endDate="2026-04-02 18:20:00 -0700"
  />
  <Record
    type="HKQuantityTypeIdentifierHeartRate"
    unit="count/min"
    value="100"
    sourceName="Apple Watch"
    startDate="2026-04-02 18:05:00 -0700"
    endDate="2026-04-02 18:05:00 -0700"
  />
  <Record
    type="HKQuantityTypeIdentifierHeartRate"
    unit="count/min"
    value="110"
    sourceName="Apple Watch"
    startDate="2026-04-02 18:10:00 -0700"
    endDate="2026-04-02 18:10:00 -0700"
  />
  <Record
    type="HKQuantityTypeIdentifierActiveEnergyBurned"
    unit="kcal"
    value="50"
    sourceName="Apple Watch"
    startDate="2026-04-02 18:00:00 -0700"
    endDate="2026-04-02 18:20:00 -0700"
  />
  <Record
    type="HKQuantityTypeIdentifierBasalEnergyBurned"
    unit="kcal"
    value="12"
    sourceName="Apple Watch"
    startDate="2026-04-02 18:00:00 -0700"
    endDate="2026-04-02 18:20:00 -0700"
  />
</HealthData>
"""


def test_find_latest_export_prefers_newest_nested_file(tmp_path, monkeypatch):
    files_dir = tmp_path / "files"
    files_dir.mkdir()
    root_export = files_dir / "export.xml"
    nested_dir = files_dir / "apple_health_export"
    nested_dir.mkdir()
    nested_export = nested_dir / "export.xml"

    root_export.write_text("<HealthData locale='en_US'></HealthData>", encoding="utf-8")
    nested_export.write_text("<HealthData locale='en_US'></HealthData>", encoding="utf-8")
    nested_export.touch()

    monkeypatch.setattr(Config, "FILES_DIR", files_dir)

    assert AppleHealthImporter.find_latest_export() == nested_export.resolve()


def test_importer_parses_workout_stats_and_record_fallbacks(tmp_path):
    xml_path = tmp_path / "export.xml"
    db_path = tmp_path / "apple_health.db"
    xml_path.write_text(APPLE_HEALTH_EXPORT, encoding="utf-8")

    db = AppleHealthDatabase(str(db_path))
    importer = AppleHealthImporter(db=db)

    stats = importer.import_from_file(xml_path)
    assert stats == {"workouts": 2}

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT activity_type, duration_seconds, active_calories, total_calories, avg_heart_rate, max_heart_rate
            FROM workouts
            ORDER BY started_at ASC
            """
        )
        rows = [dict(row) for row in cursor.fetchall()]

    assert rows[0]["activity_type"] == "run"
    assert rows[0]["duration_seconds"] == 1800
    assert rows[0]["active_calories"] == 300
    assert rows[0]["total_calories"] == 320
    assert rows[0]["avg_heart_rate"] == 152
    assert rows[0]["max_heart_rate"] == 178

    assert rows[1]["activity_type"] == "walk"
    assert rows[1]["duration_seconds"] == 1200
    assert rows[1]["active_calories"] == 50
    assert rows[1]["total_calories"] == 62
    assert rows[1]["avg_heart_rate"] == 105
    assert rows[1]["max_heart_rate"] == 110


def test_importer_is_idempotent_on_reimport(tmp_path):
    xml_path = tmp_path / "export.xml"
    db_path = tmp_path / "apple_health.db"
    xml_path.write_text(APPLE_HEALTH_EXPORT, encoding="utf-8")

    db = AppleHealthDatabase(str(db_path))
    importer = AppleHealthImporter(db=db)

    importer.import_from_file(xml_path)
    importer.import_from_file(xml_path)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM workouts")
        assert cursor.fetchone()[0] == 2


def test_importer_prefers_external_uuid_for_workout_id(tmp_path):
    xml_path = tmp_path / "export.xml"
    db_path = tmp_path / "apple_health.db"
    xml_path.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_US">
  <Workout workoutActivityType="HKWorkoutActivityTypeWalking" duration="22" durationUnit="min"
    sourceName="Oura" creationDate="2023-11-13 23:22:19 -0700"
    startDate="2022-08-21 08:57:00 -0700" endDate="2022-08-21 09:19:00 -0700">
    <MetadataEntry key="HKExternalUUID" value="oura-workout-272c6e69-1bd4-458a-a13b-ef8a3485e6a8"/>
  </Workout>
</HealthData>
""",
        encoding="utf-8",
    )

    db = AppleHealthDatabase(str(db_path))
    importer = AppleHealthImporter(db=db)
    importer.import_from_file(xml_path)

    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM workouts")
        assert cursor.fetchone()[0] == "oura-workout-272c6e69-1bd4-458a-a13b-ef8a3485e6a8"
