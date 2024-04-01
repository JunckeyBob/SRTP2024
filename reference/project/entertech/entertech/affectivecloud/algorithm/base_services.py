# 基础服务类型
BaseServiceType = str


# 基础服务
class BaseServices(object):

    # 脑电
    EEG: BaseServiceType = 'eeg'

    # 心率
    HR: BaseServiceType = 'hr-v2'
