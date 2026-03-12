import random
import asyncio
from typing import TYPE_CHECKING

from src.systems.time import Month, Year, MonthStamp
from src.classes.core.avatar import Avatar, Gender
from src.sim.avatar_awake import process_awakening
from src.classes.age import Age
from src.systems.cultivation import Realm
from src.classes.core.world import World
from src.classes.event import Event, is_null_event
from src.classes.ai import llm_ai
from src.utils.name_generator import get_random_name
from src.utils.config import CONFIG
from src.run.log import get_logger
from src.systems.fortune import try_trigger_fortune
from src.systems.fortune import try_trigger_misfortune
from src.systems.random_minor_event import try_trigger_random_minor_event
from src.systems.sect_random_event import try_trigger_sect_random_event
from src.classes.celestial_phenomenon import get_random_celestial_phenomenon
from src.classes.long_term_objective import process_avatar_long_term_objective
from src.classes.death import handle_death
from src.classes.death_reason import DeathReason, DeathType
from src.i18n import t
from src.classes.observe import get_avatar_observation_radius
from src.classes.environment.region import CultivateRegion, CityRegion
from src.classes.birth import process_births
from src.classes.nickname import process_avatar_nickname
from src.classes.backstory import process_avatar_backstory
from src.classes.relation.relation_resolver import RelationResolver
from src.classes.relation.relations import update_second_degree_relations
from src.classes.sect_decider import SectDecider

SECT_THINKING_INTERVAL_YEARS = 5

class Simulator:
    def __init__(self, world: World):
        self.world = world
        self.awakening_rate = CONFIG.game.npc_awakening_rate_per_month  # 娴犲酣鍘ょ純顔芥瀮娴犳儼顕伴崣鏈淧C濮ｅ繑婀€鐟欏鍟嬮悳鍥风礄閸戔€叉眽閺呭宕屾穱顔硷紜閿?
        self.can_interrupt_major = getattr(CONFIG.game, 'can_interrupt_major_events', False)
        
        from src.sim.managers.sect_manager import SectManager
        self.sect_manager = SectManager(world)

    def _phase_update_perception_and_knowledge(self, living_avatars: list[Avatar]):
        """
        閹扮喓鐓￠弴瀛樻煀闂冭埖顔岄敍?
        1. 閸╄桨绨幇鐔虹叀閼煎啫娲块弴瀛樻煀 known_regions
        2. 閼奉亜濮╅崡鐘冲祦閺冪姳瀵屽ú鐐茬盎閿涘牆顩ч弸婊嗗殰瀹歌鲸鐥呴張澶嬬鎼存粣绱?
        """
        events = []
        # 1. 缂傛挸鐡ㄨぐ鎾冲閺堝绀婃惔婊呮畱鐟欐帟澹奍D
        avatars_with_home = set()
        # ...
        cultivate_regions = [
            r for r in self.world.map.regions.values() 
            if isinstance(r, CultivateRegion)
        ]
        
        for r in cultivate_regions:
            if r.host_avatar:
                avatars_with_home.add(r.host_avatar.id)

        # 2. 闁秴宸婚幍鈧張澶婄摠濞叉槒顫楅懝?
        for avatar in living_avatars:
            # ...
            # 鐠侊紕鐣婚幇鐔虹叀閸楀﹤绶為敍鍫熸禆閸濆牓銆戠捄婵堫瀲閿?
            radius = get_avatar_observation_radius(avatar)
            
            # ...
            # 閼惧嘲褰囬懠鍐ㄦ纯閸愬懐娈戦張澶嬫櫏閸ф劖鐖?
            start_x = max(0, avatar.pos_x - radius)
            end_x = min(self.world.map.width - 1, avatar.pos_x + radius)
            start_y = max(0, avatar.pos_y - radius)
            end_y = min(self.world.map.height - 1, avatar.pos_y + radius)

            # 閺€鍫曟肠閹扮喓鐓￠崚鎵畱閸栧搫鐓?
            observed_regions = set()
            for x in range(start_x, end_x + 1):
                for y in range(start_y, end_y + 1):
                    # 鐠烘繄顬囬崚銈呯暰閿涙碍娴栭崫鍫ャ€戠捄婵堫瀲
                    if abs(x - avatar.pos_x) + abs(y - avatar.pos_y) <= radius:
                        tile = self.world.map.get_tile(x, y)
                        if tile.region:
                            observed_regions.add(tile.region)

            # 閺囧瓨鏌婄拋銈囩叀娑撳氦鍤滈崝銊ュ窗閹?
            for region in observed_regions:
                # 閺囧瓨鏌?known_regions
                avatar.known_regions.add(region.id)
                
                # 閼奉亜濮╅崡鐘冲祦闁槒绶?
                # 閸欘亝婀佽ぐ鎿勭窗閺勵垯鎱ㄩ悙鐓庡隘閸?+ 閺冪姳瀵?+ 閼奉亜绻侀弮鐘崇鎼?閺冩儼袝閸?
                if isinstance(region, CultivateRegion):
                    if region.host_avatar is None:
                        if avatar.id not in avatars_with_home:
                            # 閸楃姵宓?
                            avatar.occupy_region(region)
                            avatars_with_home.add(avatar.id)
                            # 鐠佹澘缍嶆禍瀣╂
                            event = Event(
                                self.world.month_stamp,
                                t("{avatar_name} passed by {region_name}, found it ownerless, and occupied it.", 
                                  avatar_name=avatar.name, region_name=region.name),
                                related_avatars=[avatar.id]
                            )
                            events.append(event)
        return events

    async def _phase_decide_actions(self, living_avatars: list[Avatar]):
        """
        閸愬磭鐡ラ梼鑸殿唽閿涙矮绮庣€靛綊娓剁憰浣规煀鐠佲€冲灊閻ㄥ嫯顫楅懝鑼剁殶閻?AI閿涘牆缍嬮崜宥嗘￥閸斻劋缍旀稉鏃€妫ょ拋鈥冲灊閿涘绱?
        鐏?AI 閻ㄥ嫬鍠呯粵鏍波閺嬫粌濮炴潪鎴掕礋鐟欐帟澹婇惃鍕吀閸掓帡鎽奸妴?
        """
        avatars_to_decide = []
        for avatar in living_avatars:
            if avatar.current_action is None and not avatar.has_plans():
                avatars_to_decide.append(avatar)
        if not avatars_to_decide:
            return
        ai = llm_ai
        decide_results = await ai.decide(self.world, avatars_to_decide)
        for avatar, result in decide_results.items():
            action_name_params_pairs, avatar_thinking, short_term_objective, _event = result
            # 娴犲懎鍙嗛梼鐔活吀閸掓帪绱濇稉宥呮躬濮濄倕顦╁ǎ璇插瀵偓婵绨ㄦ禒璁圭礉闁灝鍘ゆ稉搴㈠絹娴溿倝妯佸▓鐢稿櫢婢?
            avatar.load_decide_result_chain(action_name_params_pairs, avatar_thinking, short_term_objective)

    def _phase_commit_next_plans(self, living_avatars: list[Avatar]):
        """
        閹绘劒姘﹂梼鑸殿唽閿涙矮璐熺粚娲＝鐟欐帟澹婇幓鎰唉鐠佲€冲灊娑擃厾娈戞稉瀣╃娑擃亜褰查幍褑顢戦崝銊ょ稊閿涘矁绻戦崶鐐茬磻婵绨ㄦ禒鍫曟肠閸氬牄鈧?
        """
        events = []
        for avatar in living_avatars:
            if avatar.current_action is None:
                start_event = avatar.commit_next_plan()
                if start_event is not None and not is_null_event(start_event):
                    events.append(start_event)
        return events

    async def _phase_execute_actions(self, living_avatars: list[Avatar]):
        """
        閹笛嗩攽闂冭埖顔岄敍姘腹鏉╂稑缍嬮崜宥呭З娴ｆ粣绱濋弨顖涘瘮閸氬本婀€闁炬儳绱￠幎銏犲窗閸楄櫕妞傜紒鎾剁暬閿涘矁绻戦崶鐐存埂闂傜繝楠囬悽鐔烘畱娴滃娆㈤妴?
        """
        events = []
        MAX_LOCAL_ROUNDS = CONFIG.game.max_action_rounds_per_turn
        
        # Round 1: 閸忋劌鎲抽幍褑顢戞稉鈧▎?
        avatars_needing_retry = set()
        for avatar in living_avatars:
            try:
                new_events = await avatar.tick_action()
                if new_events:
                    events.extend(new_events)
                
                # 濡偓閺屻儲妲搁崥锔芥箒閺傛澘濮╂担婊€楠囬悽鐕傜礄閹躲垹宕?鏉╃偞瀚戦敍澶涚礉婵″倹鐏夐張澶婂灟閸旂姴鍙嗘稉瀣╃鏉?
                # 濞夈劍鍓伴敍姝礽ck_action 閸愬懘鍎村鎻掝槱閻炲棙鐖ｇ拋鐗堢闂勩倝鈧槒绶敍灞肩矌瑜版挸濮╂担婊冨絺閻㈢喎鍨忛幑銏℃閹靛秳绱版穱婵堟殌 True
                if getattr(avatar, "_new_action_set_this_step", False):
                    avatars_needing_retry.add(avatar)
            except Exception as e:
                # 鐠佹澘缍嶇拠锔剧矎闁挎瑨顕ら弮銉ョ箶
                get_logger().logger.error(f"Avatar {avatar.name}({avatar.id}) tick_action failed: {e}", exc_info=True)
                # 绾喕绻氭稉宥勭窗鏉╂稑鍙嗛柌宥堢槸闁槒绶?
                if hasattr(avatar, "_new_action_set_this_step"):
                     avatar._new_action_set_this_step = False

        # Round 2+: 娴犲懏澧界悰灞炬箒閺傛澘濮╂担婊呮畱鐟欐帟澹婇敍宀勪缉閸忓秵妫ゆ潏婊嗩潡閼规煡鍣告径宥嗗⒔鐞?
        round_count = 1
        while avatars_needing_retry and round_count < MAX_LOCAL_ROUNDS:
            current_avatars = list(avatars_needing_retry)
            avatars_needing_retry.clear()
            
            for avatar in current_avatars:
                try:
                    new_events = await avatar.tick_action()
                    if new_events:
                        events.extend(new_events)
                    
                    # 閸愬秵顐煎Λ鈧弻?
                    if getattr(avatar, "_new_action_set_this_step", False):
                        avatars_needing_retry.add(avatar)
                except Exception as e:
                    get_logger().logger.error(f"Avatar {avatar.name}({avatar.id}) retry tick_action failed: {e}", exc_info=True)
                    if hasattr(avatar, "_new_action_set_this_step"):
                        avatar._new_action_set_this_step = False
            
            round_count += 1
            
        return events

    def _phase_resolve_death(self, living_avatars: list[Avatar]):
        """
        缂佹挾鐣诲璁抽閿?
        - 閹存ɑ鏋熷璁抽瀹告彃婀?Action 娑擃厾绮ㄧ粻?
        - 濮濄倖妞傞崜鈺€绗呴惃?avatars 闁姤妲哥€涙ɑ妞块惃鍕剁礉閸欘亪娓跺Λ鈧弻銉╂姜閹存ɑ鏋熼崶鐘电閿涘牆顩ч懓浣诡劥閵嗕浇顫﹂崝銊﹀竴鐞涒偓閿?
        
        濞夈劍鍓伴敍姘洤閺嬫粌褰傞悳鐗堫劥娴溾槄绱濇导姘矤娴肩姴鍙嗛惃?living_avatars 閸掓銆冩稉顓犘╅梽銈忕礉闁灝鍘ら崥搴ｇ敾闂冭埖顔岀紒褏鐢绘径鍕倞閵?
        """
        events = []
        dead_avatars = []
        
        for avatar in living_avatars:
            is_dead = False
            death_reason: DeathReason | None = None
            
            # 娴兼ê鍘涢崚銈呯暰闁插秳婵€閿涘牆褰查懗鑺ユЦ鐞氼偄濮╅弫鍫熺亯鐎佃壈鍤ч敍?
            if avatar.hp.cur <= 0:
                is_dead = True
                death_reason = DeathReason(DeathType.SERIOUS_INJURY)
            # 閸忚埖顐奸崚銈呯暰鐎靛灝鍘?
            elif avatar.death_by_old_age():
                is_dead = True
                death_reason = DeathReason(DeathType.OLD_AGE)
                
            if is_dead and death_reason:
                event = Event(self.world.month_stamp, f"{avatar.name}{death_reason}", related_avatars=[avatar.id])
                events.append(event)
                handle_death(self.world, avatar, death_reason)
                dead_avatars.append(avatar)
        
        # 娴犲骸缍嬮崜宥呯穿閻劎娈戦崚妤勩€冩稉顓犘╅梽銈忕礉绾喕绻氶崥搴ｇ敾 Phase 娑撳秴鍟€婢跺嫮鎮?
        for dead in dead_avatars:
            if dead in living_avatars:
                living_avatars.remove(dead)
                
        return events

    def _phase_update_age_and_birth(self, living_avatars: list[Avatar]):
        """
        閺囧瓨鏌婄€涙ɑ妞跨憴鎺曞楠炴挳绶為敍灞借嫙娴犮儰绔寸€规碍顩ч悳鍥╂晸閹存劖鏌婃穱顔硷紜閿涘矁绻戦崶鐐存埂闂傜繝楠囬悽鐔烘畱娴滃娆㈤梿鍡楁値閵?
        """
        events = []
        for avatar in living_avatars:
            avatar.update_age(self.world.month_stamp)
            
        # 1. 閸戔€叉眽缁狅紕鎮婇敍姘閻炲棜鈧焦顒撮崙鈥叉眽
        self.world.mortal_manager.cleanup_dead_mortals(self.world.month_stamp)
        
        # 2. 閸戔€叉眽鐟欏鍟?(鐞涒偓閼?+ 闁插海鏁?
        awakening_events = process_awakening(self.world)
        if awakening_events:
            events.extend(awakening_events)
            
        # 3. 闁挷鑽嗛悽鐔风摍
        birth_events = process_births(self.world)
        if birth_events:
            events.extend(birth_events)
            
        return events

    async def _phase_passive_effects(self, living_avatars: list[Avatar]):
        """
        鐞氼偄濮╃紒鎾剁暬闂冭埖顔岄敍?
        - 婢跺嫮鎮婃稉纭呭祩鏉╁洦婀?
        - 閺囧瓨鏌婇弮鍫曟？閺佸牊鐏夐敍鍫濐洤HP閸ョ偛顦查敍?
        - 鐟欙箑褰傛總鍥海閿涘牓娼崝銊ょ稊閿?
        """
        events = []
        for avatar in living_avatars:
            # 1. 婢跺嫮鎮婃稉纭呭祩鏉╁洦婀?
            avatar.process_elixir_expiration(int(self.world.month_stamp))
            # 2. 閺囧瓨鏌婄悮顐㈠З閺佸牊鐏?(婵′径P閸ョ偛顦?
            avatar.update_time_effect()
        
        # 鏉╁洦鎶ら幒澶夌瑝鎼存棁顫﹂崝銊︹偓浣风皑娴犺埖澧﹂弬顓犳畱鐟欐帟澹?
        target_avatars = [
            avatar for avatar in living_avatars 
            if avatar.can_trigger_world_event
        ]
        
        # 娴ｈ法鏁?gather 楠炴儼顢戠憴锕€褰傛總鍥海閸滃矂婀佹潻?
        tasks_fortune = [try_trigger_fortune(avatar) for avatar in target_avatars]
        tasks_misfortune = [try_trigger_misfortune(avatar) for avatar in target_avatars]
        results = await asyncio.gather(*(tasks_fortune + tasks_misfortune))
        
        events.extend([e for res in results if res for e in res])
                
        return events
    
    async def _phase_random_minor_events(self, living_avatars: list[Avatar]):
        """
        闂呭繑婧€鐏忓繋绨ㄧ憴锕€褰傞梼鑸殿唽
        """
        target_avatars = [av for av in living_avatars if av.can_trigger_world_event]
        tasks = [try_trigger_random_minor_event(av, self.world) for av in target_avatars]
        results = await asyncio.gather(*tasks)
        return [e for e in results if e]

    async def _phase_sect_random_event(self):
        event = await try_trigger_sect_random_event(self.world)
        return [event] if event else []

    async def _phase_sect_yearly_thinking(self):
        """
        鐎规妫獮鏉戝閹繆鈧啴妯佸▓纰夌礄濮ｅ繐鍕?閺堝牞绱濇稉鏂挎躬鐎规妫弨璺哄弳缂佹挾鐣绘稊瀣倵閹笛嗩攽閿涘鈧?
        """
        if self.world.month_stamp.get_month() != Month.JANUARY:
            return []
        current_year = int(self.world.month_stamp.get_year())
        start_year = int(getattr(self.world, "start_year", current_year))
        if current_year < start_year:
            return []
        if (current_year - start_year) % SECT_THINKING_INTERVAL_YEARS != 0:
            return []

        sect_context = getattr(self.world, "sect_context", None)
        active_sects = (
            sect_context.get_active_sects()
            if sect_context is not None
            else (getattr(self.world, "existed_sects", []) or [])
        )
        if not active_sects:
            return []

        event_storage = getattr(getattr(self.world, "event_manager", None), "_storage", None)
        if event_storage is None:
            return []

        from src.classes.core.sect import get_sect_decision_context
        events: list[Event] = []

        async def _decide_one(sect):
            try:
                ctx = get_sect_decision_context(
                    sect=sect,
                    world=self.world,
                    event_storage=event_storage,
                )
                sect.yearly_thinking = await SectDecider.decide(sect, ctx, self.world)
                events.append(
                    Event(
                        self.world.month_stamp,
                        t("game.sect_thinking_event", sect_name=sect.name, thinking=sect.yearly_thinking),
                        related_sects=[int(sect.id)],
                    )
                )
            except Exception as e:
                get_logger().logger.error(
                    "Sect yearly thinking failed for %s(%s): %s",
                    getattr(sect, "name", "unknown"),
                    getattr(sect, "id", "unknown"),
                    e,
                    exc_info=True,
                )

        await asyncio.gather(*[_decide_one(sect) for sect in active_sects])
        return events

    async def _phase_nickname_generation(self, living_avatars: list[Avatar]):
        """
        缂佹澘褰块悽鐔稿灇闂冭埖顔?
        """
        # 楠炶泛褰傞幍褑顢?
        tasks = [process_avatar_nickname(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_backstory_generation(self, living_avatars: list[Avatar]):
        """
        闊偂绗橀悽鐔稿灇闂冭埖顔岄敍?
        閹垫儳鍤幍鈧張澶婄毣閺堫亞鏁撻幋鎰煩娑撴牜娈戠€涙ɑ妞跨憴鎺曞閿涘苯鑻熼崣鎴︽▎婵夌偠鐨熼悽?LLM 閻㈢喐鍨氶妴?
        """
        avatars_to_process = [av for av in living_avatars if av.backstory is None]
        if not avatars_to_process:
            return
            
        tasks = [process_avatar_backstory(avatar) for avatar in avatars_to_process]
        await asyncio.gather(*tasks)

    async def _phase_long_term_objective_thinking(self, living_avatars: list[Avatar]):
        """
        闂€鎸庢埂閻╊喗鐖ｉ幀婵娾偓鍐▉濞?
        濡偓閺屻儴顫楅懝鍙夋Ц閸氾箓娓剁憰浣烘晸閹?閺囧瓨鏌婇梹鎸庢埂閻╊喗鐖?
        """
        # 楠炶泛褰傞幍褑顢?
        tasks = [process_avatar_long_term_objective(avatar) for avatar in living_avatars]
        results = await asyncio.gather(*tasks)
        
        events = [e for e in results if e]
        return events
    
    async def _phase_process_gatherings(self):
        """
        Gathering 缂佹挾鐣婚梼鑸殿唽閿?
        濡偓閺屻儱鑻熼幍褑顢戝▔銊ュ斀閻ㄥ嫬顦挎禍楦夸粵闂嗗棔绨ㄦ禒璁圭礄婵″倹濯块崡鏍︾窗閵嗕礁銇囧В鏃傜搼閿涘鈧?
        """
        # 缁楊兛绔撮獮缈犵瑝鐟欙箑褰傞懕姘舵肠娴滃娆㈤敍宀€绮版禍鍫濆絺閼茶尙绱﹂崘?
        if self.world.month_stamp.get_year() <= self.world.start_year:
            return []

        return await self.world.gathering_manager.check_and_run_all(self.world)
    
    def _phase_update_celestial_phenomenon(self):
        """
        閺囧瓨鏌婃径鈺佹勾閻忓灚婧€閿?
        - 濡偓閺屻儱缍嬮崜宥呫亯鐠炩剝妲搁崥锕€鍩岄張?
        - 婵″倹鐏夐崚鐗堟埂閿涘苯鍨梾蹇旀簚闁瀚ㄩ弬鏉裤亯鐠?
        - 閻㈢喐鍨氭稉鏍櫕娴滃娆㈢拋鏉跨秿婢垛晞钖勯崣妯哄
        
        婢垛晞钖勯崣妯哄閺冭埖婧€閿?
        - 閸掓繂顫愰獮缈犲敜閿涘牆顩?00楠炶揪绱?閺堝牏鐝涢崡鍐茬磻婵顑囨稉鈧稉顏勩亯鐠?
        - 濮ｅ粴楠炶揪绱欒ぐ鎾冲婢垛晞钖勯幐鍥х暰閻ㄥ嫭瀵旂紒顓熸闂傝揪绱氶崣妯哄娑撯偓濞?
        """
        events = []
        current_year = self.world.month_stamp.get_year()
        current_month = self.world.month_stamp.get_month()
        
        # 濡偓閺屻儲妲搁崥锕傛付鐟曚礁鍨垫慨瀣閹存牗娲块弬鏉裤亯鐠?
        # 1. 婵″倹鐏夊▽鈩冩箒婢垛晞钖?(閸掓繂顫愰崠?
        # 2. 婵″倹鐏夐張澶娿亯鐠炩€茬瑬閸掔増婀?(濮ｅ繐鍕炬稉鈧張鍫燁梾閺?
        should_update = False
        is_init = False
        
        if self.world.current_phenomenon is None:
            should_update = True
            is_init = True
        elif current_month == Month.JANUARY:
            elapsed_years = current_year - self.world.phenomenon_start_year
            if elapsed_years >= self.world.current_phenomenon.duration_years:
                should_update = True

        if should_update:
            old_phenomenon = self.world.current_phenomenon
            new_phenomenon = get_random_celestial_phenomenon()
            
            if new_phenomenon:
                self.world.current_phenomenon = new_phenomenon
                self.world.phenomenon_start_year = current_year
                
                desc = ""
                if is_init:
                    desc = t("world_creation_phenomenon", name=new_phenomenon.name, desc=new_phenomenon.desc)
                else:
                    desc = t("phenomenon_change", old_name=old_phenomenon.name, new_name=new_phenomenon.name, new_desc=new_phenomenon.desc)
                
                event = Event(
                    self.world.month_stamp,
                    desc,
                    related_avatars=None
                )
                events.append(event)
        
        return events

    def _phase_update_region_prosperity(self):
        """
        濮ｅ繑婀€閸╁骸绔剁换浣藉闯鎼达箒鍤滈悞鑸典划婢?
        """
        for region in self.world.map.regions.values():
            if isinstance(region, CityRegion):
                region.change_prosperity(1)

    def _phase_log_events(self, events):
        """
        鐏忓棔绨ㄦ禒璺哄晸閸忋儲妫╄箛妞尖偓?
        """
        logger = get_logger().logger
        for event in events:
            logger.info("EVENT: %s", str(event))

    def _phase_process_interactions(self, events: list[Event]):
        """
        婢跺嫮鎮婃禍瀣╂娑擃厾娈戞禍銈勭鞍闁槒绶敍?
        闁秴宸婚幍鈧張澶夌皑娴犺绱濇俊鍌涚亯娴滃娆㈠☉澶婂挤婢舵矮閲滅憴鎺曞閿涘矁鍤滈崝銊︽纯閺傛媽绻栨禍娑滎潡閼硅弓绠ｉ梻瀵告畱娴溿倓绨扮拋鈩冩殶閵?
        """
        for event in events:
            if not event.related_avatars or len(event.related_avatars) < 2:
                continue
            
            # 閸欘亝婀佽ぐ鎾茬皑娴犺埖绉归崣?>=2 娑擃亣顫楅懝鍙夋閹靛秷顫嬫稉杞版唉娴?
            for aid in event.related_avatars:
                avatar = self.world.avatar_manager.get_avatar(aid)
                if avatar:
                    avatar.process_interaction_from_event(event)

    def _phase_handle_interactions(self, events: list[Event], processed_ids: set[str]):
        """
        娴犲簼绨ㄦ禒璺哄灙鐞涖劋鑵戦幓鎰絿鐏忔碍婀径鍕倞鏉╁洨娈戞禍銈勭鞍娴滃娆㈤敍灞借嫙閺囧瓨鏌婃禍銈勭鞍鐠佲剝鏆熼妴?
        """
        new_interactions = []
        for e in events:
            if e.id not in processed_ids:
                if e.related_avatars and len(e.related_avatars) >= 2:
                    new_interactions.append(e)
                processed_ids.add(e.id)
        
        if new_interactions:
            self._phase_process_interactions(new_interactions)

    async def _phase_evolve_relations(self, living_avatars: list[Avatar]):
        """
        閸忓磭閮村鏂垮闂冭埖顔岄敍姘梾閺屻儱鑻熸径鍕倞濠娐ゅ喕閺夆€叉閻ㄥ嫯顫楅懝鎻掑彠缁褰夐崠?
        """
        pairs_to_resolve = []
        processed_pairs = set() # (id1, id2) id1 < id2
        
        for avatar in living_avatars:
            target_ids = list(avatar.relation_interaction_states.keys())
            
            for target_id in target_ids:
                state = avatar.relation_interaction_states[target_id]
                target = self.world.avatar_manager.get_avatar(target_id)
                
                if target is None or target.is_dead:
                    continue

                # 閸掋倕鐣鹃弰顖氭儊鐟欙箑褰?
                threshold = CONFIG.social.relation_check_threshold
                if state["count"] >= threshold:
                    # 绾喕绻氶崬顖欑閹?
                    id1, id2 = sorted([str(avatar.id), str(target.id)])
                    pair_key = (id1, id2)
                    
                    if pair_key not in processed_pairs:
                        processed_pairs.add(pair_key)
                        pairs_to_resolve.append((avatar, target))
                        
                        # 闁插秶鐤嗛崣灞炬煙閻ㄥ嫯顓搁弫鏉挎珤閿涘矂妲诲銏ゅ櫢婢跺秷袝閸?
                        # 1. 闁插秶鐤?A 娓?
                        state["count"] = 0
                        state["checked_times"] += 1
                        
                        # 2. 闁插秶鐤?B 娓?
                        t_state = target.relation_interaction_states[str(avatar.id)]
                        t_state["count"] = 0
                        t_state["checked_times"] += 1
        
        events = []
        if pairs_to_resolve:
            # 閹靛綊鍣洪獮璺哄絺婢跺嫮鎮婇敍灞借嫙閻╁瓨甯撮弨鍫曟肠鏉╂柨娲栭惃鍕皑娴?
            relation_events = await RelationResolver.run_batch(pairs_to_resolve)
            if relation_events:
                events.extend(relation_events)
            
        return events

    async def step(self):
        """
        閸撳秷绻樻稉鈧稉顏呮闂傚瓨顒為敍鍫滅娑擃亝婀€閿涘绱?
        1.  閹扮喓鐓℃稉搴ゎ吇閻儲娲块弬甯礄閸欏﹨鍤滈崝銊ュ窗閹诡喗绀婃惔婊愮礆
        2.  闂€鎸庢埂閻╊喗鐖ｉ幀婵娾偓?
        3.  Gathering 婢舵矮姹夐懕姘舵肠缂佹挾鐣?
        4.  閸愬磭鐡ラ梼鑸殿唽 (AI 闁瀚ㄩ崝銊ょ稊)
        5.  閹绘劒姘﹂梼鑸殿唽 (瀵偓婵澧界悰灞藉З娴?
        6.  閹笛嗩攽闂冭埖顔?(閸斻劋缍?Tick)
        7.  婢跺嫮鎮婇崚婵囶劄娴溿倓绨扮拋鈩冩殶 (閻劋绨崥搴ｇ敾閸忓磭閮村鏂垮)
        8.  閸忓磭閮村鏂垮闂冭埖顔?
        9.  缂佹挾鐣诲璁抽
        10. 楠炴挳绶炴稉搴㈡煀閻?
        11. 闊偂绗橀悽鐔稿灇
        12. 鐞氼偄濮╃紒鎾剁暬 (娑撶宓傞妴浣规闂傚瓨鏅ラ弸婧库偓浣割殞闁?
        13. 闂呭繑婧€鐏忓繋绨?
        14. 缂佹澘褰块悽鐔稿灇
        15. 婢垛晛婀撮悘鍨簚閺囧瓨鏌?
        16. 閸╁骸绔剁换浣藉闯鎼达附娲块弬?
        17. 婢跺嫮鎮婇崜鈺€缍戞禍銈勭鞍鐠佲剝鏆?(婵″倸顨岄柆鍥﹂獓閻㈢喓娈戞禍銈勭鞍)
        18. (濮ｅ繐鍕?閺? 閺囧瓨鏌婄拋锛勭暬閸忓磭閮?(娴滃矂妯侀崗宕囬兇)
        19. (濮ｅ繐鍕?閺? 閺囧瓨鏌婂婊冨礋
        20. (濮ｅ繐鍕?閺? 濞撳懐鎮婇悽鍙樼艾閺冨爼妫挎稊鍛扮箼閼板矁顫﹂柆妤€绻曢惃鍕劥閼?
        21. 瑜版帗銆傛稉搴㈡闂傚瓨甯规潻?
        """
        # 0. 缂傛挸鐡ㄩ張顒佹箑鐎涙ɑ妞跨憴鎺曞閸掓銆?(閸︺劌鎮楃紒顓㈡▉濞堝吀鑵戞径宥囨暏閿涘苯鑻熼崷銊︻劥娴滐繝妯佸▓鐢垫樊閹?
        living_avatars = self.world.avatar_manager.get_living_avatars()

        events: list[Event] = []
        processed_event_ids: set[str] = set()

        # 1. 閹扮喓鐓℃稉搴ゎ吇閻儲娲块弬?
        events.extend(self._phase_update_perception_and_knowledge(living_avatars))

        # 2. 闂€鎸庢埂閻╊喗鐖ｉ幀婵娾偓?
        events.extend(await self._phase_long_term_objective_thinking(living_avatars))

        # 3. Gathering 缂佹挾鐣?
        events.extend(await self._phase_process_gatherings())

        # 4. 閸愬磭鐡ラ梼鑸殿唽
        await self._phase_decide_actions(living_avatars)

        # 5. 閹绘劒姘﹂梼鑸殿唽
        events.extend(self._phase_commit_next_plans(living_avatars))

        # 6. 閹笛嗩攽闂冭埖顔?
        events.extend(await self._phase_execute_actions(living_avatars))

        # 7. 婢跺嫮鎮婇崚婵囶劄娴溿倓绨扮拋鈩冩殶
        self._phase_handle_interactions(events, processed_event_ids)

        # 8. 閸忓磭閮村鏂垮
        events.extend(await self._phase_evolve_relations(living_avatars))

        # 9. 缂佹挾鐣诲璁抽 (濞夈劍鍓伴敍姘劃婢跺嫪绱版穱顔芥暭 living_avatars 閸掓銆?
        events.extend(self._phase_resolve_death(living_avatars))

        # 10. 楠炴挳绶炴稉搴㈡煀閻?
        events.extend(self._phase_update_age_and_birth(living_avatars))

        # 11. 闊偂绗橀悽鐔稿灇
        await self._phase_backstory_generation(living_avatars)

        # 12. 鐞氼偄濮╃紒鎾剁暬
        events.extend(await self._phase_passive_effects(living_avatars))

        # 13. 闂呭繑婧€鐏忓繋绨?
        events.extend(await self._phase_random_minor_events(living_avatars))
        events.extend(await self._phase_sect_random_event())

        # 14. 缂佹澘褰块悽鐔稿灇
        events.extend(await self._phase_nickname_generation(living_avatars))

        # 15. 閺囧瓨鏌婃径鈺佹勾閻忓灚婧€
        events.extend(self._phase_update_celestial_phenomenon())

        # 16. 閺囧瓨鏌婇崺搴＄缁讳浇宕虫惔?
        self._phase_update_region_prosperity()

        # 17. 婢跺嫮鎮婇崜鈺€缍戦梼鑸殿唽閻ㄥ嫪姘︽禍鎺曨吀閺?
        self._phase_handle_interactions(events, processed_event_ids)

        # 18. (濮ｅ繐鍕?閺? 閺囧瓨鏌婄拋锛勭暬閸忓磭閮?(娴滃矂妯侀崗宕囬兇)
        self._phase_update_calculated_relations(living_avatars)

        ###########
        # 濮ｅ繐鍕鹃幍褑顢戦惃鍕攽娑?
        ###########
        
        # 19. (濮ｅ繐鍕?閺? 閺囧瓨鏌婂婊冨礋娑撳骸鐣婚梻銊х波缁?
        if self.world.month_stamp.get_month() == Month.JANUARY:
            # 娴ｈ法鏁?World 娑撳﹣绗呴弬鍥ㄦ纯閺傜増顪侀崡鏇礉鐎规妫婊冪唨娴滃孩婀扮仦鈧崥顖滄暏鐎规妫?
            self.world.ranking_manager.update_rankings_with_world(self.world, living_avatars)

            # 鐎规妫獮鏉戝缂佹挾鐣婚敍鍫濆◢閸旀稖瀵栭崶缈犵瑢閻忕數鐓堕敍?
            sect_events = self.sect_manager.update_sects()
            if sect_events:
                events.extend(sect_events)
            events.extend(await self._phase_sect_yearly_thinking())
        
        # 20. (濮ｅ繐鍕?閺? 濞撳懐鎮婇悽鍙樼艾閺冨爼妫挎稊鍛扮箼閼板矁顫﹂柆妤€绻曢惃鍕劥閼?
        if self.world.month_stamp.get_month() == Month.JANUARY:
            cleaned_count = self.world.avatar_manager.cleanup_long_dead_avatars(
                self.world.month_stamp, 
                CONFIG.game.long_dead_cleanup_years
            )
            if cleaned_count > 0:
                # 鐠佹澘缍嶉弮銉ョ箶閿涘奔绲炬稉宥勯獓閻㈢喐鐖堕幋蹇撳敶娴滃娆?
                get_logger().logger.info(f"Cleaned up {cleaned_count} long-dead avatars.")

        # 21. 瑜版帗銆傛稉搴㈡闂傚瓨甯规潻?
        return self._finalize_step(events)

    def _phase_update_calculated_relations(self, living_avatars: list[Avatar]):
        """
        濮ｅ繐鍕?1 閺堝牆鍩涢弬鏉垮弿閺堝秷顫楅懝鑼畱娴滃矂妯侀崗宕囬兇缂傛挸鐡?
        """
        # 娴犲懎婀?1 閺堝牊澧界悰?
        if self.world.month_stamp.get_month() != Month.JANUARY:
            return

        for avatar in living_avatars:
            update_second_degree_relations(avatar)

    def _finalize_step(self, events: list[Event]) -> list[Event]:
        """
        閺堫剝鐤嗗銉ㄧ箻閻ㄥ嫭娓剁紒鍫濈秺濡楋綇绱伴崢濠氬櫢閵嗕礁鍙嗘惔鎾扁偓浣瑰ⅵ閺冦儱绻旈妴浣瑰腹鏉╂稒妞傞梻娣偓?
        """
        # 0. 娑撳搫鎯庨悽銊ㄦ嫹闊亞娈?Avatar 鐠佹澘缍嶅В蹇旀箑韫囶偆鍙?
        for avatar in self.world.avatar_manager.avatars.values():
            if avatar.enable_metrics_tracking:
                avatar.record_metrics()

        # 1. 閸╄桨绨?ID 閸樺鍣搁敍鍫ユЩ濮濄垹鎮撴稉鈧稉顏冪皑娴犺泛顕挒陇顫︽径姘偧濞ｈ濮為敍?
        unique_events: dict[str, Event] = {}
        for e in events:
            if e.id not in unique_events:
                unique_events[e.id] = e
        final_events = list(unique_events.values())

        # 2. 缂佺喍绔撮崘娆忓弳娴滃娆㈢粻锛勬倞閸?
        if self.world.event_manager:
            for e in final_events:
                self.world.event_manager.add_event(e)
        
        # 3. 鐠佹澘缍嶉弮銉ョ箶
        self._phase_log_events(final_events)

        # 4. 閺冨爼妫块幒銊ㄧ箻
        self.world.month_stamp = self.world.month_stamp + 1
        
        return final_events
