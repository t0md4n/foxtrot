import pytest
from unittest.mock import patch
import os
from main import parse_tags_from_csv, validate_mailchimp_config


class TestParseTagsFromCSV:
    """Tests for parse_tags_from_csv() function."""

    def test_standard_tags(self):
        """Standard CSV format tags are parsed correctly."""
        result = parse_tags_from_csv('"Tag1","Tag2","Tag3"')
        assert result == ["Tag1", "Tag2", "Tag3"]

    def test_single_tag(self):
        """Single tag is parsed correctly."""
        result = parse_tags_from_csv('"SingleTag"')
        assert result == ["SingleTag"]

    def test_empty_string(self):
        """Empty string returns empty list."""
        assert parse_tags_from_csv("") == []

    def test_whitespace_only(self):
        """Whitespace-only returns empty list."""
        assert parse_tags_from_csv("   ") == []

    def test_none_input(self):
        """None input returns empty list."""
        assert parse_tags_from_csv(None) == []

    def test_non_string_integer(self):
        """Integer input returns empty list."""
        assert parse_tags_from_csv(123) == []

    def test_non_string_list(self):
        """List input returns empty list."""
        assert parse_tags_from_csv(["tag"]) == []

    def test_tags_with_spaces(self):
        """Tags with spaces in names are preserved."""
        result = parse_tags_from_csv('"Tag One","Tag Two"')
        assert result == ["Tag One", "Tag Two"]


class TestValidateMailchimpConfig:
    """Tests for validate_mailchimp_config() function."""

    def test_valid_config(self):
        """Valid config returns API key and audience ID."""
        with patch.dict(os.environ, {
            "MAILCHIMP_API_KEY": "abc123-us1",
            "MAILCHIMP_AUDIENCE_ID": "list123"
        }, clear=True):
            api_key, audience_id = validate_mailchimp_config()
            assert api_key == "abc123-us1"
            assert audience_id == "list123"

    def test_missing_api_key(self):
        """Missing API key raises ValueError."""
        with patch.dict(os.environ, {
            "MAILCHIMP_AUDIENCE_ID": "list123"
        }, clear=True):
            with pytest.raises(ValueError, match="MAILCHIMP_API_KEY"):
                validate_mailchimp_config()

    def test_missing_audience_id(self):
        """Missing audience ID raises ValueError."""
        with patch.dict(os.environ, {
            "MAILCHIMP_API_KEY": "abc123-us1"
        }, clear=True):
            with pytest.raises(ValueError, match="MAILCHIMP_AUDIENCE_ID"):
                validate_mailchimp_config()

    def test_invalid_api_key_format(self):
        """API key without hyphen raises ValueError."""
        with patch.dict(os.environ, {
            "MAILCHIMP_API_KEY": "invalidkeyformat",
            "MAILCHIMP_AUDIENCE_ID": "list123"
        }, clear=True):
            with pytest.raises(ValueError, match="Invalid MAILCHIMP_API_KEY format"):
                validate_mailchimp_config()


class TestFlaskRoutes:
    """Tests for Flask routes."""

    def test_index_route(self, client):
        """GET / returns 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_dashboard_route(self, client):
        """GET /dashboard returns 200."""
        response = client.get("/dashboard")
        assert response.status_code == 200

    def test_mailchimp_route(self, client):
        """GET /mailchimp returns 200."""
        response = client.get("/mailchimp")
        assert response.status_code == 200

    def test_sharepoint_route(self, client):
        """GET /sharepoint returns 200."""
        response = client.get("/sharepoint")
        assert response.status_code == 200

    def test_process_route_no_files(self, client):
        """POST /process with no files redirects."""
        response = client.post("/process", data={"action": "generate_zip"})
        assert response.status_code == 302
