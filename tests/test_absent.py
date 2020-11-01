from json_serde._utils import Absent, AbsentType


def test_absent():
    assert AbsentType() is Absent
    assert AbsentType() == Absent
    assert None is not Absent
    assert '' is not Absent
    assert False is not Absent
    assert not Absent

    assert repr(Absent) == 'Absent'
    assert str(Absent) == 'Absent'
