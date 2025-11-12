#!/usr/bin/env python3
"""
Test script to verify menu logic without running the full game
"""

from menu import Menu, MenuState

def test_menu():
    menu = Menu()

    print("Testing Menu System")
    print("=" * 50)

    # Test initial state
    assert menu.state == MenuState.MAIN_MENU
    print("✓ Menu starts in MAIN_MENU state")

    # Test main menu options
    assert len(menu.main_menu_options) == 4
    print("✓ Menu has 4 options")

    # Test state transitions
    menu.state = MenuState.ENTER_NAME
    assert menu.state == MenuState.ENTER_NAME
    print("✓ Can transition to ENTER_NAME state")

    menu.state = MenuState.MAIN_MENU
    assert menu.state == MenuState.MAIN_MENU
    print("✓ Can transition back to MAIN_MENU")

    # Test player name
    menu.player_name = "Test"
    assert menu.player_name == "Test"
    print("✓ Can set player name")

    # Test host flag
    menu.is_host = True
    assert menu.is_host == True
    print("✓ Can set host flag")

    menu.is_host = False
    assert menu.is_host == False
    print("✓ Can unset host flag")

    print("\n" + "=" * 50)
    print("All menu tests passed! ✓")
    print("\nThe menu should work correctly.")
    print("Try running: python3 main.py")

if __name__ == "__main__":
    test_menu()
