"""Tests for the auth models."""

from homeassistant.auth import auth_manager_from_config, models, permissions
from homeassistant.core import HomeAssistant


def test_owner_fetching_owner_permissions() -> None:
    """Test we fetch the owner permissions for an owner user."""
    group = models.Group(name="Test Group", policy={})
    owner = models.User(
        name="Test User", perm_lookup=None, groups=[group], is_owner=True
    )
    assert owner.permissions is permissions.OwnerPermissions


def test_permissions_merged() -> None:
    """Test we merge the groups permissions."""
    group = models.Group(
        name="Test Group", policy={"entities": {"domains": {"switch": True}}}
    )
    group2 = models.Group(
        name="Test Group", policy={"entities": {"entity_ids": {"light.kitchen": True}}}
    )
    user = models.User(name="Test User", perm_lookup=None, groups=[group, group2])
    # Make sure we cache instance
    assert user.permissions is user.permissions

    assert user.permissions.check_entity("switch.bla", "read") is True
    assert user.permissions.check_entity("light.kitchen", "read") is True
    assert user.permissions.check_entity("light.not_kitchen", "read") is False


def test_cache_cleared_on_group_change() -> None:
    """Test we clear the cache when a group changes."""
    group = models.Group(
        name="Test Group", policy={"entities": {"domains": {"switch": True}}}
    )
    admin_group = models.Group(
        name="Admin group", id=models.GROUP_ID_ADMIN, policy={"entities": {}}
    )
    user = models.User(
        name="Test User", perm_lookup=None, groups=[group], is_active=True
    )
    # Make sure we cache instance
    assert user.permissions is user.permissions

    # Make sure we cache is_admin
    assert user.is_admin is user.is_admin
    assert user.is_active is True

    user.groups = []
    assert user.groups == []
    assert user.is_admin is False

    user.is_owner = True
    assert user.is_admin is True
    user.is_owner = False

    assert user.is_admin is False
    user.groups = [admin_group]
    assert user.is_admin is True

    user.is_active = False
    assert user.is_admin is False


async def test_hass_username(hass: HomeAssistant) -> None:
    """Test that hass_username correctly pulls the username from the hass provider."""
    manager = await auth_manager_from_config(hass, [{"type": "homeassistant"}], [])
    hass_provider = manager.auth_providers[0]
    credentials = await hass_provider.async_get_or_create_credentials(
        {"username": "hello"}
    )
    user = await manager.async_get_or_create_user(credentials)
    assert user.hass_username == "hello"
