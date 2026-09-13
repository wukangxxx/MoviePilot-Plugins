"""
UI配置模块
负责生成插件的配置表单和详情页面
"""
from typing import List, Dict, Any, Tuple
from app.core.config import settings
from app.db.subscribe_oper import SubscribeOper
from app.schemas.types import MediaType
from app.log import logger
from app.db import SessionFactory
from sqlalchemy import text


class UIConfig:
    """UI配置管理类"""

    @staticmethod
    def get_subscribe_options() -> List[Dict[str, Any]]:
        """
        获取订阅选项列表（电影和电视剧）
        :return: 订阅选项列表 [{"title": "显示名", "value": id}, ...]
        """
        try:
            with SessionFactory() as db:
                subscribes = SubscribeOper(db=db).list("N,R")
            if not subscribes:
                return []

            options = []
            for s in subscribes:
                type_label = "[剧]" if s.type == MediaType.TV.value else "[影]"
                if s.type == MediaType.TV.value:
                    display = f"{type_label} {s.name} ({s.year}) S{s.season or 1}" if s.year else f"{type_label} {s.name} S{s.season or 1}"
                else:
                    display = f"{type_label} {s.name} ({s.year})" if s.year else f"{type_label} {s.name}"
                options.append({"title": display, "value": s.id})
            return options
        except Exception as e:
            logger.error(f"获取订阅列表失败: {e}")
            return []

    @staticmethod
    def get_site_name_options() -> List[Dict[str, Any]]:
        """
        获取站点名称列表（用于多选）
        items: [{'title': '站点名', 'value': '站点名'}]
        """
        try:
            with SessionFactory() as db:
                rows = db.execute(text("SELECT name FROM site ORDER BY name")).fetchall()
            items = []
            for r in rows:
                name = str(r[0])
                if not name:
                    continue
                items.append({"title": name, "value": name})
            return items
        except Exception as e:
            logger.error(f"获取站点列表失败: {e}")
            return []

    @staticmethod
    def _section_title(text: str) -> Dict[str, Any]:
        """生成一个区块小标题行（用于主界面的分区标识）。"""
        return {
            'component': 'VRow',
            'content': [{
                'component': 'VCol',
                'props': {'cols': 12},
                'content': [{
                    'component': 'div',
                    'props': {'class': 'text-h6 font-weight-bold mt-2'},
                    'text': text
                }]
            }]
        }

    @staticmethod
    def _alert(text: str, atype: str = 'info') -> Dict[str, Any]:
        """生成一个整宽提示条。"""
        return {
            'component': 'VRow',
            'content': [{
                'component': 'VCol',
                'props': {'cols': 12},
                'content': [{
                    'component': 'VAlert',
                    'props': {'type': atype, 'variant': 'tonal', 'text': text}
                }]
            }]
        }

    @staticmethod
    def _tab_item(value: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """把若干行包装成一个 Tab 页内容。"""
        return {
            'component': 'VWindowItem',
            'props': {'value': value},
            'content': list(rows)
        }

    @staticmethod
    def get_form() -> Tuple[List[dict], Dict[str, Any]]:
        """
        获取插件配置表单

        v1.8.0 版式：
            主界面 = 插件基本功能配置 + 115网盘信息配置
            其下按「订阅 / 签到 / 盘搜 / 癫影 / 影巢 / 金山文档」分 Tab 管理

        :return: (表单schema, 默认配置)
        """
        subscribe_options = UIConfig.get_subscribe_options()
        site_name_items = UIConfig.get_site_name_options()

        # ============ 主界面：插件基本功能配置 ============
        basic_rows: List[Dict[str, Any]] = [
            # 基本开关 + 执行周期
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'enabled', 'label': '启用插件'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'notify', 'label': '发送通知'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'block_system_subscribe', 'label': '屏蔽系统订阅'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'onlyonce', 'label': '立即运行'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{
                         'component': 'VCronField',
                         'props': {
                             'model': 'cron',
                             'label': '执行周期（Cron）',
                             'placeholder': '30 2,10,18 * * *',
                             'hint': '5段 Cron：分 时 日 月 周；最小间隔 4 小时（低于 4 小时自动回退 30 */4 * * *）。例：30 2,10,18 * * * 表示2点、10点、18点的30分执行',
                             'persistent-hint': True,
                             'clearable': True
                         }
                     }]}
                ]
            },
            # 风控防护（批量转存与单次上限）
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'max_transfer_per_sync', 'label': '单次同步上限', 'type': 'number', 'placeholder': '50', 'hint': '每次同步最多转存文件数', 'persistent-hint': True}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'batch_size', 'label': '批量转存大小', 'type': 'number', 'placeholder': '20', 'hint': '每批转存文件数', 'persistent-hint': True}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'max_transfer_links', 'label': '单订阅最大转存链接数', 'type': 'number', 'placeholder': '5', 'hint': '转存前先检测链接有效性，对有效链接最多转存这么多个', 'persistent-hint': True}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'skip_other_season_dirs', 'label': '多季剧集快速转存', 'hint': '跳过其他季目录以减少API调用，资源搜索不到时需要关闭', 'persistent-hint': True}}]}
                ]
            }
        ]

        # ============ 主界面：115网盘信息配置 ============
        p115_rows: List[Dict[str, Any]] = [
            UIConfig._alert('115网盘配置：请从浏览器获取Cookie（包含UID、CID、SEID、KID等字段）', 'warning'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'save_path', 'label': '电视剧转存目录', 'placeholder': '/我的接收/MoviePilot/TV'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'movie_save_path', 'label': '电影转存目录', 'placeholder': '/我的接收/MoviePilot/Movie'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'cookies', 'label': '115 Cookie', 'type': 'password', 'placeholder': 'UID=xxx; CID=xxx; SEID=xxx'}}]}
                ]
            }
        ]

        # ============ Tab 1：订阅 ============
        subscribe_tab: List[Dict[str, Any]] = [
            UIConfig._alert('订阅：决定本插件处理哪些 MoviePilot 订阅，以及任务期间如何临时屏蔽系统订阅。'),
            # 订阅过滤模式
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12, 'md': 4},
                    'content': [{
                        'component': 'VSelect',
                        'props': {
                            'model': 'subscribe_filter_mode',
                            'label': '订阅过滤模式',
                            'items': [
                                {'title': '排除模式（处理除勾选外的全部订阅）', 'value': 'exclude'},
                                {'title': '指定模式（仅处理勾选的订阅）', 'value': 'include'}
                            ],
                            'hint': '以PT订阅为主、网盘为辅时建议用指定模式，只勾选少数需要网盘补充的订阅',
                            'persistent-hint': True
                        }
                    }]
                }]
            },
            # 排除订阅
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{'component': 'VSelect', 'props': {'model': 'exclude_subscribes', 'label': '排除订阅（排除模式下生效：选择不需要本插件处理的订阅）',
                        'multiple': True, 'chips': True, 'clearable': True, 'closable-chips': True, 'items': subscribe_options}}]
                }]
            },
            # 指定订阅
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{'component': 'VSelect', 'props': {'model': 'include_subscribes', 'label': '指定订阅（指定模式下生效：仅勾选的订阅由本插件处理）',
                        'multiple': True, 'chips': True, 'clearable': True, 'closable-chips': True, 'items': subscribe_options}}]
                }]
            },
            # 取消屏蔽后的站点选择 / 窗口期 / 延迟分钟
            {
                'component': 'VRow',
                'content': [
                    {
                        'component': 'VCol',
                        'props': {'cols': 12, 'md': 6},
                        'content': [{
                            'component': 'VSelect',
                            'props': {
                                'model': 'unblock_site_names',
                                'label': '取消屏蔽后订阅站点选择（多选）',
                                'items': site_name_items,
                                'multiple': True,
                                'chips': True,
                                'clearable': True,
                                'closable-chips': True,
                                'hint': '为空表示禁用窗口：始终保持屏蔽（仅115网盘）',
                                'persistent-hint': True
                            }
                        }]
                    },
                    {
                        'component': 'VCol',
                        'props': {'cols': 12, 'md': 3},
                        'content': [{
                            'component': 'VTextField',
                            'props': {
                                'model': 'unblock_window_hours',
                                'label': '取消屏蔽窗口期（小时）',
                                'type': 'number',
                                'placeholder': '2',
                                'hint': '设为0表示禁用窗口：始终保持屏蔽（仅115网盘）',
                                'persistent-hint': True,
                                'clearable': True
                            }
                        }]
                    },
                    {
                        'component': 'VCol',
                        'props': {'cols': 12, 'md': 3},
                        'content': [{
                            'component': 'VTextField',
                            'props': {
                                'model': 'unblock_delay_minutes',
                                'label': '每天最后一次任务后延迟（分钟）',
                                'type': 'number',
                                'placeholder': '5',
                                'hint': '设为-1表示禁用窗口：始终保持屏蔽（仅115网盘）；否则23:00兜底恢复系统订阅',
                                'persistent-hint': True,
                                'clearable': True
                            }
                        }]
                    }
                ]
            },
            # 搜索源优先级
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{
                        'component': 'VSelect',
                        'props': {
                            'model': 'search_source_order',
                            'label': '搜索源优先级（按选择顺序排序）',
                            'items': [
                                {'title': '癫影 (Dian115)', 'value': 'dian115'},
                                {'title': 'PanSou (盘搜)', 'value': 'pansou'},
                                {'title': 'KDocs (在线文档库)', 'value': 'kdocs'}
                            ],
                            'multiple': True,
                            'chips': True,
                            'clearable': True,
                            'closable-chips': True,
                            'hint': '按选择的先后顺序依次搜索，前面的源搜到结果就不再查询后面的；留空使用默认优先级 癫影 > 盘搜 > 金山文档；未选入的已启用源会自动排在末尾',
                            'persistent-hint': True
                        }
                    }]
                }]
            }
        ]

        # ============ Tab 2：签到 ============
        checkin_tab: List[Dict[str, Any]] = [
            UIConfig._alert('签到：独立于订阅搜索的每日签到任务，支持 115 网盘签到与癫影签到/转盘抽奖。'
                            '癫影签到需要在「癫影」页签配置账号，115 签到使用上方「115网盘信息配置」的 Cookie。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'checkin_enabled', 'label': '启用签到'}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'checkin_notify', 'label': '签到通知'}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 2},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'checkin_onlyonce', 'label': '立即签到'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{
                         'component': 'VCronField',
                         'props': {
                             'model': 'checkin_cron',
                             'label': '签到周期（Cron）',
                             'placeholder': '30 8 * * *',
                             'hint': '留空则跟随插件主周期执行；建议每天固定时间执行一次即可',
                             'persistent-hint': True,
                             'clearable': True
                         }
                     }]}
                ]
            },
            UIConfig._alert('115 网盘签到：每日签到领取枫叶，需要已配置 115 Cookie。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'p115_checkin_enabled', 'label': '启用 115 签到'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 8},
                     'content': [{'component': 'VAlert', 'props': {'type': 'info', 'variant': 'tonal',
                         'text': '115 签到依赖上方「115网盘信息配置」中的 Cookie，无需额外账号。'}}]}
                ]
            },
            UIConfig._alert('癫影签到与转盘：需要已在「癫影」页签填写账号密码；转盘会消耗积分，请按需设置次数。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'dian115_checkin_enabled', 'label': '启用癫影签到'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VSelect', 'props': {
                         'model': 'dian115_checkin_mode',
                         'label': '签到模式',
                         'items': [
                             {'title': '普通签到', 'value': 'normal'},
                             {'title': '运气签到（随机倍数，积分波动大）', 'value': 'lucky'}
                         ],
                         'hint': '运气签到会按随机倍数结算积分，可能高于或低于普通签到',
                         'persistent-hint': True
                     }}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'dian115_lottery_enabled', 'label': '启用转盘抽奖'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {
                         'model': 'dian115_lottery_count',
                         'label': '转盘次数',
                         'type': 'number',
                         'placeholder': '0',
                         'hint': '每次签到最多转 20 次，超出自动收敛',
                         'persistent-hint': True
                     }}]}
                ]
            }
        ]

        # ============ Tab 3：盘搜 ============
        pansou_tab: List[Dict[str, Any]] = [
            UIConfig._alert('PanSou搜索服务：网盘资源聚合搜索，用于搜索115网盘分享链接。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'pansou_enabled', 'label': '启用 PanSou'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'pansou_url', 'label': 'PanSou API 地址', 'placeholder': 'https://your-pansou-api.com'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'pansou_channels', 'label': 'TG 搜索频道', 'placeholder': '频道,用逗号分隔'}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'pansou_auth_enabled', 'label': '启用认证'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'pansou_username', 'label': 'PanSou 用户名', 'placeholder': '启用认证时填写'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'pansou_password', 'label': 'PanSou 密码', 'type': 'password', 'placeholder': '启用认证时填写', 'clearable': True}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'pansou_check_enabled', 'label': '启用 PanSou 链接有效性检测(全渠道)',
                         'hint': '转存前先用 PanSou 校验链接是否有效，可减少无效转存', 'persistent-hint': True}}]}
                ]
            }
        ]

        # ============ Tab 4：癫影 ============
        dian115_tab: List[Dict[str, Any]] = [
            UIConfig._alert('癫影（Dian115）：按 TMDB ID 精准查询 115 网盘分享链接，准确度高于关键词搜索。'
                            '实测站点资源绝大多数需要积分才能拿到链接，下方可开启自动解锁并设置预算。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'dian115_enabled', 'label': '启用癫影搜索'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'dian115_email', 'label': '癫影账号（邮箱）', 'placeholder': '注册邮箱'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'dian115_password', 'label': '癫影密码', 'type': 'password', 'placeholder': '登录密码', 'clearable': True}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{'component': 'VTextarea', 'props': {
                        'model': 'dian115_token',
                        'label': '浏览器 Token（__Host-portal_token）',
                        'rows': 2,
                        'placeholder': '浏览器登录 m.dian115.com 后，F12 → 应用 → Cookie → 复制 __Host-portal_token 的值',
                        'clearable': True,
                        'hint': '站点已对「邮箱+密码」自动登录开启人机验证，必须通过浏览器手动登录获取 Token；有效期约 24 小时，过期后需重新获取',
                        'persistent-hint': True
                    }}]
                }]
            },
            UIConfig._alert('说明：癫影搜索与签到都必须依赖上方 Token（账号密码仅供记录与 Token 归属校验）。'
                            'Token 过期时日志会提示「unauthorized / 未登录」，重新粘贴即可，无需重启插件。', 'warning'),
            UIConfig._alert('重要实测结论：癫影的 115 链接 100% 需要积分解锁，而解锁接口带 Cloudflare 人机验证，'
                            '精简客户端无法自动通过（会返回 turnstile_failed，不会误扣积分）。'
                            '因此本插件的癫影搜索源在不解锁时返回 0 条；建议把癫影主要用于「签到 + 转盘」赚积分，'
                            '搜索仍走「盘搜」。', 'info'),
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{'component': 'VSwitch', 'props': {
                        'model': 'dian115_auto_unlock',
                        'label': '自动消耗积分解锁资源（需解锁接口可用）',
                        'hint': '默认关闭。开启后遇到收费条目会尝试解锁；若站点要求人机验证则自动跳过并记日志，'
                                '不会扣分也不会中断任务。'
                    }}]
                }]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'dian115_max_unlock_points', 'label': '单次任务解锁总预算', 'type': 'number', 'placeholder': '50', 'hint': '一轮同步任务最多消耗的积分总和'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'dian115_max_points_per_sub', 'label': '单个订阅解锁预算', 'type': 'number', 'placeholder': '20', 'hint': '处理单个订阅时允许消耗的最大积分'}}]}
                ]
            }
        ]

        # ============ Tab 5：影巢（已失效） ============
        hdhive_tab: List[Dict[str, Any]] = [
            UIConfig._alert('影巢（HDHive）站点已停止服务，相关配置项保留仅供兼容，'
                            '即使勾选也不会参与搜索调度。建议启用「盘搜」或「癫影」作为搜索源。', 'error'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'hdhive_enabled', 'label': '启用 HDHive（已失效）'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VSelect', 'props': {'model': 'hdhive_query_mode', 'label': '查询模式',
                         'items': [{'title': 'API 模式', 'value': 'api'}, {'title': 'Playwright 模式', 'value': 'playwright'}]}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_client_id', 'label': 'HDHive Client ID', 'placeholder': 'OpenAPI 应用公开 ID（app_xxx）', 'clearable': True}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_api_key', 'label': 'HDHive 应用 Secret', 'type': 'password', 'placeholder': 'OpenAPI 应用 Secret（X-API-Key）', 'clearable': True}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_redirect_uri', 'label': '回调地址', 'placeholder': '须与 OpenAPI 应用配置完全一致', 'clearable': True}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_auth_code', 'label': '授权码', 'placeholder': '授权后回调地址中的 code 参数', 'hint': '一次性使用，换取 Token 成功后自动清空', 'persistent-hint': True, 'clearable': True}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_username', 'label': 'HDHive 用户名', 'placeholder': 'Playwright 模式下需要'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_password', 'label': 'HDHive 密码', 'type': 'password', 'placeholder': 'Playwright 模式下需要', 'clearable': True}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'hdhive_auto_unlock', 'label': '自动解锁资源', 'hint': '关闭时仅查询免费资源'}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_max_unlock_points', 'label': '累计解锁总预算', 'type': 'number', 'placeholder': '50', 'hint': '一次任务最多允许消耗的积分总和'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'hdhive_max_points_per_sub', 'label': '单订阅解锁预算', 'type': 'number', 'placeholder': '20', 'hint': '处理单个订阅时允许消耗的最大积分'}}]}
                ]
            }
        ]

        # ============ Tab 6：金山文档 ============
        kdocs_tab: List[Dict[str, Any]] = [
            UIConfig._alert('KDocs在线文档库：读取金山文档在线表格中的资源分享信息并匹配网盘链接。'
                            '需配置 Skill Token；留空文档链接时使用默认文档库。'),
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VSwitch', 'props': {'model': 'kdocs_enabled', 'label': '启用在线文档库'}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 4},
                     'content': [{'component': 'VTextField', 'props': {'model': 'kdocs_token', 'label': 'Skill Token', 'type': 'password', 'placeholder': 'KDocs Skill Token', 'clearable': True,
                         'hint': '获取：kdocs.cn 登录后右上角头像菜单「金山文档Skill」复制Token', 'persistent-hint': True}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 2},
                     'content': [{'component': 'VTextField', 'props': {'model': 'kdocs_cache_ttl_hours', 'label': '缓存(小时)', 'type': 'number', 'placeholder': '6'}}]},
                    {'component': 'VCol', 'props': {'cols': 6, 'md': 3},
                     'content': [{'component': 'VTextField', 'props': {'model': 'kdocs_batch_rows', 'label': '分批行数', 'type': 'number', 'placeholder': '1000', 'hint': '单批拉取行数上限1000'}}]}
                ]
            },
            {
                'component': 'VRow',
                'content': [{
                    'component': 'VCol',
                    'props': {'cols': 12},
                    'content': [{'component': 'VTextarea', 'props': {'model': 'kdocs_doc_urls', 'label': '文档库分享链接（每行一个）', 'rows': 3, 'placeholder': 'https://www.kdocs.cn/l/xxxx', 'clearable': True,
                        'hint': '留空使用默认文档库；可维护多个文档库同时匹配', 'persistent-hint': True}}]
                }]
            },
            {
                'component': 'VRow',
                'content': [
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VTextField', 'props': {'model': 'kdocs_cookie', 'label': '金山文档 Cookie', 'type': 'password', 'placeholder': '浏览器登录 kdocs.cn 后 F12 复制 Cookie', 'clearable': True}}]},
                    {'component': 'VCol', 'props': {'cols': 12, 'md': 6},
                     'content': [{'component': 'VAlert', 'props': {'type': 'info', 'variant': 'tonal', 'text': 'Cookie获取教程：浏览器登录 kdocs.cn → F12 打开开发者工具 → 网络/应用面板复制 Cookie 请求头'}}]}
                ]
            }
        ]

        # ============ 组装：主界面 + Tab 区 ============
        form_schema = [
            {
                'component': 'VForm',
                'content': [
                    # 插件总说明
                    UIConfig._alert('自动搜索115网盘资源并转存缺失的电影和剧集，需配置115 Cookie和搜索服务。'
                                    '执行周期支持任意 Cron 表达式，最小间隔限制 4 小时（更频繁的配置将回退为每 4 小时执行）。'),

                    # 一、插件基本功能配置
                    UIConfig._section_title('插件基本功能配置'),
                    *basic_rows,

                    # 二、115网盘信息配置
                    UIConfig._section_title('115网盘信息配置'),
                    *p115_rows,

                    # 三、功能分页
                    {
                        'component': 'VTabs',
                        'props': {
                            'model': '_tabs',
                            'style': {'margin-top': '8px', 'margin-bottom': '16px'},
                            'stacked': True,
                            'fixed-tabs': True
                        },
                        'content': [
                            {'component': 'VTab', 'props': {'value': 'subscribe_tab'}, 'text': '订阅'},
                            {'component': 'VTab', 'props': {'value': 'checkin_tab'}, 'text': '签到'},
                            {'component': 'VTab', 'props': {'value': 'pansou_tab'}, 'text': '盘搜'},
                            {'component': 'VTab', 'props': {'value': 'dian115_tab'}, 'text': '癫影'},
                            {'component': 'VTab', 'props': {'value': 'hdhive_tab'}, 'text': '影巢'},
                            {'component': 'VTab', 'props': {'value': 'kdocs_tab'}, 'text': '金山文档'}
                        ]
                    },
                    {
                        'component': 'VWindow',
                        'props': {'model': '_tabs'},
                        'content': [
                            UIConfig._tab_item('subscribe_tab', subscribe_tab),
                            UIConfig._tab_item('checkin_tab', checkin_tab),
                            UIConfig._tab_item('pansou_tab', pansou_tab),
                            UIConfig._tab_item('dian115_tab', dian115_tab),
                            UIConfig._tab_item('hdhive_tab', hdhive_tab),
                            UIConfig._tab_item('kdocs_tab', kdocs_tab)
                        ]
                    }
                ]
            }
        ]

        default_config = {
            "enabled": False,
            "notify": True,
            "onlyonce": False,
            "only_115": True,
            "cron": "30 2,10,18 * * *",

            "unblock_site_ids": [],
            "unblock_site_names": [],
            "unblock_window_hours": 1,
            "system_subscribe_window_hours": 1,
            "unblock_delay_minutes": 5,

            "save_path": "/我的接收/MoviePilot/TV",
            "movie_save_path": "/我的接收/MoviePilot/Movie",
            "cookies": "",

            # 订阅
            "search_source_order": [],
            "subscribe_filter_mode": "exclude",
            "exclude_subscribes": [],
            "include_subscribes": [],
            "block_system_subscribe": False,

            # 转存风控
            "max_transfer_per_sync": 50,
            "batch_size": 20,
            "max_transfer_links": 5,
            "skip_other_season_dirs": True,

            # 签到（v1.8.0）
            "checkin_enabled": False,
            "checkin_notify": True,
            "checkin_onlyonce": False,
            "checkin_cron": "",
            "p115_checkin_enabled": True,
            "dian115_checkin_enabled": False,
            "dian115_checkin_mode": "normal",
            "dian115_lottery_enabled": False,
            "dian115_lottery_count": 0,

            # 盘搜 PanSou
            "pansou_enabled": True,
            "pansou_url": "https://so.252035.xyz/",
            "pansou_username": "",
            "pansou_password": "",
            "pansou_auth_enabled": False,
            "pansou_channels": "QukanMovie",
            "pansou_check_enabled": True,

            # 癫影 Dian115（v1.8.0）
            "dian115_enabled": False,
            "dian115_email": "",
            "dian115_password": "",
            "dian115_token": "",
            "dian115_auto_unlock": False,
            "dian115_max_unlock_points": 50,
            "dian115_max_points_per_sub": 20,

            # 影巢 HDHive（站点已失效，仅作兼容保留）
            "nullbr_enabled": False,
            "nullbr_appid": "",
            "nullbr_api_key": "",
            "hdhive_enabled": False,
            "hdhive_query_mode": "api",
            "hdhive_api_key": "",
            "hdhive_client_id": "",
            "hdhive_redirect_uri": "",
            "hdhive_auth_code": "",
            "hdhive_access_token": "",
            "hdhive_refresh_token": "",
            "hdhive_token_expires_at": 0,
            "hdhive_auto_unlock": False,
            "hdhive_max_unlock_points": 50,
            "hdhive_max_points_per_sub": 20,
            "hdhive_username": "",
            "hdhive_password": "",
            "hdhive_cookie": "",
            "hdhive_auto_refresh": True,
            "hdhive_refresh_before": 86400,

            # 金山文档 KDocs
            "kdocs_enabled": False,
            "kdocs_token": "",
            "kdocs_doc_urls": "",
            "kdocs_cache_ttl_hours": 6,
            "kdocs_batch_rows": 1000,
            "kdocs_cookie": ""
        }

        return form_schema, default_config

    @staticmethod
    def get_page(history: List[dict]) -> List[dict]:
        """
        详情页内容与 1.2.4 无强耦合，保持原样即可
        """
        # 你原有的 get_page 很长，这里不做任何改动，继续沿用你现有版本即可。
        # 如果你希望我也按 1.2.4 统一“文案/按钮标题”，你告诉我我再一起改。
        from datetime import datetime

        history = history or []
        total_count = len(history)
        success_count = len([h for h in history if h.get("status") == "成功"])
        fail_count = len([h for h in history if h.get("status") == "失败"])
        movie_count = len([h for h in history if h.get("type") == "电影"])
        tv_count = len([h for h in history if h.get("type") != "电影"])

        today = datetime.now().strftime("%Y-%m-%d")
        today_count = len([h for h in history if h.get("time", "").startswith(today)])

        success_rate = f"{(success_count / total_count * 100):.1f}%" if total_count > 0 else "0%"

        sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True) if history else []
        last_sync_time = sorted_history[0].get("time", "暂无") if sorted_history else "暂无"

        stats_header = {
            'component': 'VCard',
            'props': {'class': 'mb-4'},
            'content': [{
                'component': 'VCardText',
                'content': [
                    # 第一行：统计卡片（总转存数、今日转存、成功数、失败数）
                    {
                        'component': 'VRow',
                        'content': [
                            # 总转存数
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'md': 3},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': 'primary'},
                                    'content': [{
                                        'component': 'VCardText',
                                        'props': {'class': 'text-center pa-3'},
                                        'content': [
                                            {'component': 'VIcon', 'props': {'size': 'x-large', 'class': 'mb-2'}, 'text': 'mdi-cloud-upload'},
                                            {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': str(total_count)},
                                            {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '总转存数'}
                                        ]
                                    }]
                                }]
                            },
                            # 今日转存
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'md': 3},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': 'info'},
                                    'content': [{
                                        'component': 'VCardText',
                                        'props': {'class': 'text-center pa-3'},
                                        'content': [
                                            {'component': 'VIcon', 'props': {'size': 'x-large', 'class': 'mb-2'}, 'text': 'mdi-calendar-today'},
                                            {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': str(today_count)},
                                            {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '今日转存'}
                                        ]
                                    }]
                                }]
                            },
                            # 成功数
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'md': 3},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': 'success'},
                                    'content': [{
                                        'component': 'VCardText',
                                        'props': {'class': 'text-center pa-3'},
                                        'content': [
                                            {'component': 'VIcon', 'props': {'size': 'x-large', 'class': 'mb-2'}, 'text': 'mdi-check-circle'},
                                            {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': str(success_count)},
                                            {'component': 'div', 'props': {'class': 'text-caption'}, 'text': f'成功 ({success_rate})'}
                                        ]
                                    }]
                                }]
                            },
                            # 失败数
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'md': 3},
                                'content': [{
                                    'component': 'VCard',
                                    'props': {'variant': 'tonal', 'color': 'error'},
                                    'content': [{
                                        'component': 'VCardText',
                                        'props': {'class': 'text-center pa-3'},
                                        'content': [
                                            {'component': 'VIcon', 'props': {'size': 'x-large', 'class': 'mb-2'}, 'text': 'mdi-close-circle'},
                                            {'component': 'div', 'props': {'class': 'text-h4 font-weight-bold'}, 'text': str(fail_count)},
                                            {'component': 'div', 'props': {'class': 'text-caption'}, 'text': '失败'}
                                        ]
                                    }]
                                }]
                            }
                        ]
                    },
                    # 第二行：媒体类型统计（电影数、剧集数）和最近同步时间
                    {
                        'component': 'VRow',
                        'props': {'class': 'mt-4'},
                        'content': [
                            # 电影数
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [{
                                    'component': 'div',
                                    'props': {'class': 'd-flex align-center justify-center'},
                                    'content': [
                                        {'component': 'VIcon', 'props': {'color': 'amber', 'class': 'mr-2'}, 'text': 'mdi-movie'},
                                        {'component': 'span', 'props': {'class': 'text-h6 font-weight-medium'}, 'text': str(movie_count)},
                                        {'component': 'span', 'props': {'class': 'text-caption ml-1'}, 'text': '部电影'}
                                    ]
                                }]
                            },
                            # 剧集数
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [{
                                    'component': 'div',
                                    'props': {'class': 'd-flex align-center justify-center'},
                                    'content': [
                                        {'component': 'VIcon', 'props': {'color': 'purple', 'class': 'mr-2'}, 'text': 'mdi-television-classic'},
                                        {'component': 'span', 'props': {'class': 'text-h6 font-weight-medium'}, 'text': str(tv_count)},
                                        {'component': 'span', 'props': {'class': 'text-caption ml-1'}, 'text': '集剧集'}
                                    ]
                                }]
                            },
                            # 最近同步时间
                            {
                                'component': 'VCol',
                                'props': {'cols': 4},
                                'content': [{
                                    'component': 'div',
                                    'props': {'class': 'd-flex align-center justify-center'},
                                    'content': [
                                        {'component': 'VIcon', 'props': {'color': 'cyan', 'class': 'mr-2'}, 'text': 'mdi-clock-outline'},
                                        {'component': 'span', 'props': {'class': 'text-caption'}, 'text': f'最近同步: {last_sync_time[:16] if len(last_sync_time) > 16 else last_sync_time}'}
                                    ]
                                }]
                            }
                        ]
                    },
                    # 操作按钮：立即搜索 + 清空历史记录
                    {
                        'component': 'VRow',
                        'props': {'class': 'mt-4'},
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'class': 'text-center'},
                                'content': [{
                                    'component': 'VBtn',
                                    'props': {'color': 'primary', 'variant': 'outlined', 'size': 'small', 'prepend-icon': 'mdi-magnify'},
                                    'text': '立即搜索',
                                    'events': {
                                        'click': {
                                            'api': f'/plugin/P115SubSearch/sync_subscribes?apikey={settings.API_TOKEN}',
                                            'method': 'get'
                                        }
                                    }
                                }]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 6, 'class': 'text-center'},
                                'content': [{
                                    'component': 'VBtn',
                                    'props': {'color': 'error', 'variant': 'outlined', 'size': 'small', 'prepend-icon': 'mdi-delete-sweep'},
                                    'text': '清空历史记录',
                                    'events': {
                                        'click': {
                                            'api': f'/plugin/P115SubSearch/clear_history?apikey={settings.API_TOKEN}',
                                            'method': 'post'
                                        }
                                    }
                                }]
                            }
                        ]
                    }
                ]
            }]
        }

        if not sorted_history:
            empty_state = {
                'component': 'VCard',
                'props': {'variant': 'outlined', 'class': 'mt-4'},
                'content': [{
                    'component': 'VCardText',
                    'props': {'class': 'text-center py-8'},
                    'content': [
                        {'component': 'VIcon', 'props': {'size': '64', 'color': 'grey-lighten-1', 'class': 'mb-4'}, 'text': 'mdi-inbox-outline'},
                        {'component': 'div', 'props': {'class': 'text-h6 text-grey'}, 'text': '暂无转存记录'},
                        {'component': 'div', 'props': {'class': 'text-caption text-grey-lighten-1 mt-2'}, 'text': '插件运行后会在此显示转存记录'}
                    ]
                }]
            }
            return [stats_header, empty_state]

        movie_history = [h for h in sorted_history if h.get("type") == "电影"][:50]
        tv_history = [h for h in sorted_history if h.get("type") != "电影"][:50]

        def build_history_item(h: dict) -> dict:
            status = h.get("status", "")
            media_type = h.get("type", "")
            status_color = "success" if status == "成功" else "error" if status == "失败" else "warning"
            status_icon = "mdi-check-circle" if status == "成功" else "mdi-close-circle" if status == "失败" else "mdi-help-circle"
            type_icon = "mdi-movie" if media_type == "电影" else "mdi-television-classic"
            type_color = "amber" if media_type == "电影" else "purple"
            file_name = h.get("file_name", "")

            if media_type == "电影":
                title_text = f'{h.get("title", "")} ({h.get("year", "")})'
            else:
                season = h.get("season", 0) or 0
                episode = h.get("episode", 0) or 0
                title_text = f'{h.get("title", "")} S{season:02d}E{episode:02d}'

            content_items = [
                {
                    'component': 'div',
                    'props': {'class': 'd-flex justify-space-between align-center'},
                    'content': [
                        {
                            'component': 'div',
                            'props': {'class': 'd-flex align-center'},
                            'content': [
                                {'component': 'VIcon', 'props': {'color': type_color, 'size': 'small', 'class': 'mr-2'}, 'text': type_icon},
                                {'component': 'span', 'props': {'class': 'font-weight-bold'}, 'text': title_text}
                            ]
                        },
                        {
                            'component': 'div',
                            'props': {'class': 'd-flex align-center'},
                            'content': [
                                {'component': 'VIcon', 'props': {'color': status_color, 'size': 'x-small', 'class': 'mr-1'}, 'text': status_icon},
                                {'component': 'VChip', 'props': {'color': status_color, 'size': 'x-small', 'variant': 'flat'}, 'text': status}
                            ]
                        }
                    ]
                },
                {
                    'component': 'div',
                    'props': {'class': 'd-flex align-center mt-1'},
                    'content': [
                        {'component': 'VIcon', 'props': {'size': 'x-small', 'color': 'grey', 'class': 'mr-1'}, 'text': 'mdi-clock-outline'},
                        {'component': 'span', 'props': {'class': 'text-caption text-grey'}, 'text': h.get("time", "")}
                    ]
                }
            ]

            if file_name:
                content_items.append({
                    'component': 'div',
                    'props': {'class': 'd-flex align-center mt-1'},
                    'content': [
                        {'component': 'VIcon', 'props': {'size': 'x-small', 'color': 'grey', 'class': 'mr-1'}, 'text': 'mdi-file-video'},
                        {'component': 'span', 'props': {'class': 'text-caption text-grey text-truncate'}, 'text': file_name}
                    ]
                })

            border_style = f'border-left: 3px solid var(--v-theme-{status_color}) !important;'
            return {
                'component': 'VCard',
                'props': {'class': 'mb-2', 'variant': 'outlined', 'style': border_style},
                'content': [{'component': 'VCardText', 'props': {'class': 'py-2 px-3'}, 'content': content_items}]
            }

        def build_history_list(items: List[dict], empty_text: str) -> List[dict]:
            if not items:
                return [{
                    'component': 'div',
                    'props': {'class': 'text-center py-8'},
                    'content': [
                        {'component': 'VIcon', 'props': {'size': '48', 'color': 'grey-lighten-1', 'class': 'mb-2'}, 'text': 'mdi-inbox-outline'},
                        {'component': 'div', 'props': {'class': 'text-grey'}, 'text': empty_text}
                    ]
                }]
            return [build_history_item(h) for h in items]

        expansion_panels = {
            'component': 'VExpansionPanels',
            'props': {'variant': 'accordion', 'class': 'mt-4'},
            'content': [
                {
                    'component': 'VExpansionPanel',
                    'content': [
                        {
                            'component': 'VExpansionPanelTitle',
                            'content': [
                                {'component': 'VIcon', 'props': {'color': 'amber', 'class': 'mr-3'}, 'text': 'mdi-movie'},
                                {'component': 'span', 'props': {'class': 'font-weight-bold'}, 'text': f'电影 ({len(movie_history)})'}
                            ]
                        },
                        {
                            'component': 'VExpansionPanelText',
                            'content': build_history_list(movie_history, '暂无电影转存记录')
                        }
                    ]
                },
                {
                    'component': 'VExpansionPanel',
                    'content': [
                        {
                            'component': 'VExpansionPanelTitle',
                            'content': [
                                {'component': 'VIcon', 'props': {'color': 'purple', 'class': 'mr-3'}, 'text': 'mdi-television-classic'},
                                {'component': 'span', 'props': {'class': 'font-weight-bold'}, 'text': f'剧集 ({len(tv_history)})'}
                            ]
                        },
                        {
                            'component': 'VExpansionPanelText',
                            'content': build_history_list(tv_history, '暂无剧集转存记录')
                        }
                    ]
                }
            ]
        }

        return [stats_header, expansion_panels]
