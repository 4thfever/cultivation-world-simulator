from enum import Enum

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"

    def __str__(self) -> str:
        from src.i18n import t
        return t(gender_msg_ids.get(self, self.value))

gender_msg_ids = {
    Gender.MALE: "male",
    Gender.FEMALE: "female",
}
