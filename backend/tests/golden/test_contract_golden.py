from pathlib import Path


def test_csv_contracts_keep_required_representation_rules() -> None:
    contract_directory = Path("docs/contracts")
    representation = (contract_directory / "csv-representation-v1.md").read_text(
        encoding="utf-8"
    )

    assert "UTF-8" in representation
    assert "`NA`" in representation
    assert "LF" in representation
