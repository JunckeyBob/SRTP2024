# 情感计算服务类型
AffectiveServiceType = str


# 情感计算服务
class AffectiveServices(object):

    # Base Service EEG required（依赖基础服务：EEG）
    # 注意力
    ATTENTION: AffectiveServiceType = 'attention'
    # 儿童注意力
    ATTENTION_FOR_CHILD: AffectiveServiceType = 'attention_chd'
    # 放松度
    RELAXATION: AffectiveServiceType = 'relaxation'
    # 儿童放松度
    RELAXATION_FOR_CHILD: AffectiveServiceType = 'relaxation_chd'
    # 愉悦度
    PLEASURE: AffectiveServiceType = 'pleasure'
    # 睡眠
    SLEEP: AffectiveServiceType = 'sleep'

    # Base Service HR required（依赖基础服务：HR）
    # 压力
    PRESSURE: AffectiveServiceType = 'pressure'
    # 激活度
    AROUSAL: AffectiveServiceType = 'arousal'
    # 呼吸和谐
    COHERENCE: AffectiveServiceType = 'coherence'
