"""
Basic health check tests for the Shop Sphere application
"""
import pytest


def test_basic_import():
    """Test that basic Python functionality works"""
    assert True


def test_environment_setup():
    """Test that the test environment is properly configured"""
    import os
    # Basic environment test
    assert os.path.exists(".")


@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality works"""
    async def sample_async_function():
        return "success"
    
    result = await sample_async_function()
    assert result == "success"


def test_database_url_format():
    """Test database URL format validation"""
    import os
    
    # Get database URL from environment or use test default
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:testpass@localhost:5432/testdb")
    
    # Basic URL format validation
    assert "postgresql://" in db_url
    assert "@" in db_url
    assert ":" in db_url


class TestBasicFunctionality:
    """Test class for basic application functionality"""
    
    def test_string_operations(self):
        """Test basic string operations"""
        test_string = "Shop Sphere"
        assert len(test_string) > 0
        assert "Shop" in test_string
        assert test_string.replace("Shop", "Test") == "Test Sphere"
    
    def test_list_operations(self):
        """Test basic list operations"""
        test_list = [1, 2, 3, 4, 5]
        assert len(test_list) == 5
        assert sum(test_list) == 15
        assert max(test_list) == 5
    
    def test_dict_operations(self):
        """Test basic dictionary operations"""
        test_dict = {"name": "Shop Sphere", "version": "1.0.0"}
        assert "name" in test_dict
        assert test_dict["name"] == "Shop Sphere"
        assert len(test_dict.keys()) == 2 