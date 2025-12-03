import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from processors.sp import process_sp_files, _get_column
from processors.common import CONTACT_COLUMNS


class TestGetColumn:
    """Tests for _get_column() helper function."""

    def test_finds_exact_match(self):
        """Finds column with exact name match."""
        df = pd.DataFrame({"First Name": [1], "Last Name": [2]})
        assert _get_column(df, ["First Name", "Fname"]) == "First Name"

    def test_case_insensitive_match(self):
        """Finds column case-insensitively."""
        df = pd.DataFrame({"first name": [1], "last name": [2]})
        assert _get_column(df, ["First Name", "Fname"]) == "first name"

    def test_returns_first_option_if_not_found(self):
        """Returns first option if column not found."""
        df = pd.DataFrame({"Other": [1]})
        assert _get_column(df, ["First Name", "Fname"]) == "First Name"

    def test_finds_second_option(self):
        """Finds second option if first not present."""
        df = pd.DataFrame({"Fname": [1], "Other": [2]})
        assert _get_column(df, ["First Name", "Fname"]) == "Fname"


class TestProcessSPFiles:
    """Tests for process_sp_files() function."""

    @patch("processors.sp._read_any_excel_or_csv")
    def test_uk_direct_sets_country_to_gb(self, mock_read):
        """UK_DIRECT list type sets country to GB."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["John"],
            "Last Name": ["Smith"],
            "Contact Email Address": ["john@test.com"],
            "Organisation": ["TestCo"],
            "State/Area": ["London"],
            "Technical Tags": ["patent"],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_DIRECT")

        assert result.iloc[0]["Country"] == "GB"
        assert "DIRECT client or prospect" in result.iloc[0]["Tags"]

    @patch("processors.sp._read_any_excel_or_csv")
    def test_us_direct_sets_country_to_us(self, mock_read):
        """US_DIRECT list type sets country to US."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Jane"],
            "Last Name": ["Doe"],
            "Contact Email Address": ["jane@test.com"],
            "Organisation": ["USCo"],
            "State/Area": ["CA"],
            "Technical Tags": ["tm"],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "US_DIRECT")

        assert result.iloc[0]["Country"] == "US"
        assert "US" in result.iloc[0]["Tags"]

    @patch("processors.sp._read_any_excel_or_csv")
    def test_technical_tags_converted_to_interests(self, mock_read):
        """Technical tags are converted to interest tags."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Test"],
            "Last Name": ["User"],
            "Contact Email Address": ["test@test.com"],
            "Organisation": ["Co"],
            "State/Area": ["London"],
            "Technical Tags": ["patent, trade mark"],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_DIRECT")

        tags = result.iloc[0]["Tags"]
        assert "Patent Interest" in tags
        assert "TM Interest" in tags

    @patch("processors.sp._read_any_excel_or_csv")
    def test_region_tagging_for_uk_edinburgh(self, mock_read):
        """UK lists get Edinburgh region tag."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Test"],
            "Last Name": ["User"],
            "Contact Email Address": ["test@test.com"],
            "Organisation": ["Co"],
            "State/Area": ["Edinburgh"],
            "Technical Tags": [""],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_DIRECT")

        assert "Edinburgh & South-East Scotland" in result.iloc[0]["Tags"]

    @patch("processors.sp._read_any_excel_or_csv")
    def test_uk_referrers_tags(self, mock_read):
        """UK_REFERRERS list type gets UK Referrer tag."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Test"],
            "Last Name": ["User"],
            "Contact Email Address": ["test@test.com"],
            "Organisation": ["Co"],
            "State/Area": ["Glasgow"],
            "Technical Tags": [""],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_REFERRERS")

        assert result.iloc[0]["Country"] == "GB"
        assert "UK Referrer" in result.iloc[0]["Tags"]

    @patch("processors.sp._read_any_excel_or_csv")
    def test_output_has_correct_columns(self, mock_read):
        """Output DataFrame has all required CONTACT_COLUMNS."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Test"],
            "Last Name": ["User"],
            "Contact Email Address": ["test@test.com"],
            "Organisation": ["Co"],
            "State/Area": ["London"],
            "Technical Tags": [""],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_DIRECT")

        assert list(result.columns) == CONTACT_COLUMNS

    @patch("processors.sp._read_any_excel_or_csv")
    def test_sp_source_tag_always_added(self, mock_read):
        """SP source tag is always added."""
        mock_read.return_value = pd.DataFrame({
            "First Name": ["Test"],
            "Last Name": ["User"],
            "Contact Email Address": ["test@test.com"],
            "Organisation": ["Co"],
            "State/Area": ["London"],
            "Technical Tags": [""],
        })

        result = process_sp_files(MagicMock(), "Nov 2025", "UK_DIRECT")

        assert "SP" in result.iloc[0]["Tags"]
