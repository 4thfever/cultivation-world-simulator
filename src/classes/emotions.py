from enum import Enum

class EmotionType(Enum):
    CALM = "emotion_calm"
    HAPPY = "emotion_happy"
    ANGRY = "emotion_angry"
    SAD = "emotion_sad"
    FEARFUL = "emotion_fearful"
    SURPRISED = "emotion_surprised"
    ANTICIPATING = "emotion_anticipating"
    DISGUSTED = "emotion_disgusted"
    CONFUSED = "emotion_confused"
    TIRED = "emotion_tired"

# 情绪对应的 Emoji 配置
EMOTION_EMOJIS = {
    EmotionType.CALM: "😌",
    EmotionType.HAPPY: "😄",
    EmotionType.ANGRY: "😡",
    EmotionType.SAD: "😢",
    EmotionType.FEARFUL: "😨",
    EmotionType.SURPRISED: "😲",
    EmotionType.ANTICIPATING: "🤩",
    EmotionType.DISGUSTED: "🤢",
    EmotionType.CONFUSED: "😕",
    EmotionType.TIRED: "😫",
}
