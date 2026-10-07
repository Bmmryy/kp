"""Unit tests for FlowETL automated scheduler service."""

from app.services.scheduler import SchedulerService


def test_scheduler_add_and_list():
    service = SchedulerService()
    job = service.add_schedule(
        name="Hourly Sync",
        pipeline_name="Hospital ETL",
        source_type="mysql",
        source_options={"table_name": "Patient"},
        destination_type="sqlite",
        destination_options={"path": "test.sqlite", "table_name": "patients"},
        frequency="hourly",
    )
    assert job.id is not None
    assert job.name == "Hourly Sync"
    assert job.frequency == "hourly"
    assert job.is_enabled is True
    assert job.next_run_at is not None

    jobs = service.list_schedules()
    assert len(jobs) == 1
    assert jobs[0].id == job.id


def test_scheduler_toggle():
    service = SchedulerService()
    job = service.add_schedule(
        name="Daily Backup",
        pipeline_name="Backup Pipeline",
        source_type="sqlite",
        source_options={},
        destination_type="json",
        destination_options={},
        frequency="daily",
    )
    assert job.is_enabled is True

    # Toggle off
    toggled = service.toggle_schedule(job.id)
    assert toggled.is_enabled is False
    assert toggled.next_run_at is None

    # Toggle back on
    toggled2 = service.toggle_schedule(job.id)
    assert toggled2.is_enabled is True
    assert toggled2.next_run_at is not None


def test_scheduler_delete():
    service = SchedulerService()
    job = service.add_schedule(
        name="Temp Job",
        pipeline_name="Temp",
        source_type="csv",
        source_options={},
        destination_type="json",
        destination_options={},
    )
    assert len(service.list_schedules()) == 1

    deleted = service.delete_schedule(job.id)
    assert deleted is True
    assert len(service.list_schedules()) == 0


def test_scheduler_manual_trigger():
    service = SchedulerService()
    triggered_runs = []

    def mock_runner(pipeline_name, source_type, source_options, destination_type, destination_options, loop, transformations=None):
        triggered_runs.append(pipeline_name)
        return "mock_run_123"

    class MockLoop:
        def create_task(self, coro):
            return None

    service.set_runner_callback(mock_runner, MockLoop())
    job = service.add_schedule(
        name="Auto Run",
        pipeline_name="My Pipeline",
        source_type="csv",
        source_options={},
        destination_type="json",
        destination_options={},
    )

    run_id = service.trigger_job(job.id)
    assert run_id == "mock_run_123"
    assert len(triggered_runs) == 1
    assert "[Scheduled] My Pipeline" in triggered_runs[0]
    assert job.run_count == 1


def test_scheduler_get_and_update():
    service = SchedulerService()
    job = service.add_schedule(
        name="Old Name",
        pipeline_name="Old Pipe",
        source_type="csv",
        source_options={"path": "old.csv"},
        destination_type="json",
        destination_options={"path": "old.json"},
        frequency="daily",
    )
    assert service.get_schedule(job.id) is not None
    assert service.get_schedule("nonexistent") is None

    updated = service.update_schedule(
        job.id,
        name="New Name",
        pipeline_name="New Pipe",
        frequency="hourly",
        destination_type="sqlite",
        destination_options={"path": "new.sqlite", "table_name": "dest"},
    )
    assert updated is not None
    assert updated.name == "New Name"
    assert updated.pipeline_name == "New Pipe"
    assert updated.frequency == "hourly"
    assert updated.destination_type == "sqlite"
    assert updated.destination_options["table_name"] == "dest"

    # Updating nonexistent job returns None
    assert service.update_schedule("nonexistent", name="Fail") is None

