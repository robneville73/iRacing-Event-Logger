"""Tests for SDK wrapper and focus resolution."""

import pytest

from iracing_event_logger.sdk_wrapper import (
    resolve_focus_car,
    get_driver_by_car_idx,
    car_number_and_name,
    FocusCar,
)


def test_resolve_focus_car_by_number():
    driver_info = {
        "Drivers": [
            {"CarIdx": 0, "CarNumber": "1", "UserName": "Alice"},
            {"CarIdx": 1, "CarNumber": "5", "UserName": "Bob"},
        ],
    }
    focus = resolve_focus_car(driver_info, focus_car="5")
    assert focus is not None
    assert focus.car_idx == 1
    assert focus.car_number == "5"
    assert focus.driver_name == "Bob"


def test_resolve_focus_car_by_driver():
    driver_info = {
        "Drivers": [
            {"CarIdx": 0, "CarNumber": "1", "UserName": "Alice"},
            {"CarIdx": 1, "CarNumber": "5", "UserName": "Bob"},
        ],
    }
    focus = resolve_focus_car(driver_info, focus_driver="Bob")
    assert focus is not None
    assert focus.car_idx == 1
    assert focus.car_number == "5"


def test_resolve_focus_car_not_found():
    driver_info = {"Drivers": [{"CarIdx": 0, "CarNumber": "1", "UserName": "Alice"}]}
    assert resolve_focus_car(driver_info, focus_car="99") is None
    assert resolve_focus_car(driver_info, focus_driver="Nobody") is None


def test_resolve_focus_car_no_focus_specified():
    driver_info = {"Drivers": [{"CarIdx": 0, "CarNumber": "1"}]}
    assert resolve_focus_car(driver_info, None, None) is None


def test_get_driver_by_car_idx():
    driver_info = {"Drivers": [{"CarIdx": 0, "CarNumber": "1"}, {"CarIdx": 1, "CarNumber": "5"}]}
    d = get_driver_by_car_idx(driver_info, 1)
    assert d is not None
    assert d["CarNumber"] == "5"
    assert get_driver_by_car_idx(driver_info, 99) is None


def test_car_number_and_name():
    assert car_number_and_name(None) == ("", "")
    assert car_number_and_name({"CarNumber": "5", "UserName": "Bob"}) == ("5", "Bob")
    assert car_number_and_name({"CarNumberRaw": "05", "AbbrevName": "B"}) == ("05", "B")


def test_focus_car_to_session_dict():
    f = FocusCar(car_idx=1, car_number="5", driver_name="Bob")
    d = f.to_session_dict()
    assert d["car_idx"] == 1
    assert d["car_number"] == "5"
    assert d["driver_name"] == "Bob"
