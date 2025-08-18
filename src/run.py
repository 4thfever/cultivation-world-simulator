from src.classes.avatar import Avatar, Gender
from src.classes.calendar import Month, Year

avatar = Avatar(
    name="John Doe",
    id=1,
    birth_month=Month.JANUARY,
    birth_year=Year(2000),
    age=20,
    gender=Gender.MALE
)

print(avatar)