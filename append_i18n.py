import os

zh_content = """

# Action: Play Extended
msgid "action_reading"
msgstr "读书"

msgid "action_tea_tasting"
msgstr "品茶"

msgid "action_traveling"
msgstr "游历"

msgid "action_zither_playing"
msgstr "抚琴"

msgid "action_tea_party"
msgstr "茶会"

msgid "action_chess"
msgstr "下棋"

msgid "{avatar} starts {action}"
msgstr "{avatar} 开始{action}"

msgid "{avatar} finished {action}."
msgstr "{avatar} 完成了{action}。"

msgid "gained {val} cultivation"
msgstr "若有所悟，修为增加 {val}"

msgid "breakthrough probability increased by {val:.1%}"
msgstr "心境提升，突破概率增加 {val:.1%}"
"""

en_content = """

# Action: Play Extended
msgid "action_reading"
msgstr "Reading"

msgid "action_tea_tasting"
msgstr "Tea Tasting"

msgid "action_traveling"
msgstr "Traveling"

msgid "action_zither_playing"
msgstr "Playing Zither"

msgid "action_tea_party"
msgstr "Tea Party"

msgid "action_chess"
msgstr "Chess"

msgid "{avatar} starts {action}"
msgstr "{avatar} starts {action}"

msgid "{avatar} finished {action}."
msgstr "{avatar} finished {action}."

msgid "gained {val} cultivation"
msgstr "gained {val} cultivation"

msgid "breakthrough probability increased by {val:.1%}"
msgstr "breakthrough probability increased by {val:.1%}"
"""

with open('src/i18n/locales/zh_CN/LC_MESSAGES/messages.po', 'a', encoding='utf-8') as f:
    f.write(zh_content)

with open('src/i18n/locales/en_US/LC_MESSAGES/messages.po', 'a', encoding='utf-8') as f:
    f.write(en_content)

print("Appended translations successfully.")
