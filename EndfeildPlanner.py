import streamlit as st
import pandas as pd
import pulp
import io
import math

# ================= 1. 基础数据配置 (写死在代码中) =================

# 1.1 配方数据
recipes_csv = """产物名称,产物数量,加工时间秒,设备名称,原料1名称,原料1数量,原料2名称,原料2数量
蓝铁块,1,2,精炼炉,蓝铁矿,1,,
紫晶纤维,1,2,精炼炉,紫晶矿,1,,
晶体外壳,1,2,精炼炉,源矿,1,,
碳块,1,2,精炼炉,荞花,1,,
稳定碳块,1,2,精炼炉,碳块,1,,
密制晶体,1,2,精炼炉,晶体外壳粉末,1,,
高晶纤维,1,2,精炼炉,高晶粉末,1,,
钢块,1,2,精炼炉,蓝铁块,1,,
致密晶体粉末,1,2,精炼炉,致密源石粉末,1,,
蓝铁粉末,1,2,粉碎机,蓝铁块,1,,
紫晶粉末,1,2,粉碎机,紫晶纤维,1,,
晶体外壳粉末,1,2,粉碎机,晶体外壳,1,,
碳粉末,2,2,粉碎机,碳块,1,,
荞花粉末,2,2,粉碎机,荞花,1,,
柑实粉末,2,2,粉碎机,柑实,1,,
砂叶粉末,3,2,粉碎机,砂叶,1,,
铁制零件,1,2,配件机,蓝铁块,1,,
紫晶零件,1,2,配件机,紫晶纤维,1,,
钢制零件,1,2,配件机,钢块,1,,
高晶零件,1,2,配件机,高晶纤维,1,,
蓝铁瓶,1,2,塑型机,蓝铁块,2,,
紫晶质瓶,1,2,塑型机,紫晶纤维,2,,
钢质瓶,1,2,塑型机,钢块,2,,
高晶质瓶,1,2,塑型机,高晶纤维,2,,
柑实罐头,1,10,灌装机,紫晶质瓶,5,柑实粉末,5
优质柑实罐头,1,10,灌装机,蓝铁瓶,10,柑实粉末,10
精选柑实罐头,1,10,灌装机,蓝铁瓶,10,细磨柑实粉末,10
荞愈胶囊,1,10,灌装机,紫晶质瓶,5,荞花粉末,5
优质荞愈胶囊,1,10,灌装机,蓝铁瓶,10,荞花粉末,10
精选荞愈胶囊,1,10,灌装机,蓝铁瓶,10,细磨荞花粉末,10
低容谷地电池,1,10,封装机,紫晶零件,5,源石粉末,10
中容谷地电池,1,10,封装机,铁制零件,10,源石粉末,15
高容谷地电池,1,10,封装机,铁制零件,10,致密源石粉末,15
致密蓝铁粉末,1,2,研磨机,蓝铁粉末,2,砂叶粉末,1
致密源石粉末,1,2,研磨机,源石粉末,2,砂叶粉末,1
致密晶体粉末,1,2,研磨机,晶体外壳粉末,2,砂叶粉末,1
高晶粉末,1,2,研磨机,紫晶粉末,2,砂叶粉末,1
致密碳粉末,1,2,研磨机,碳粉末,2,砂叶粉末,1
细磨柑实粉末,1,2,研磨机,柑实粉末,2,砂叶粉末,1
细磨荞花粉末,1,2,研磨机,荞花粉末,2,砂叶粉末,1
源石粉末,2,2,粉碎机,源矿,1,,
"""
df_recipes = pd.read_csv(io.StringIO(recipes_csv)).fillna(0)
df_recipes.set_index('产物名称', inplace=False)

# 1.2 物品价值
ITEM_PRICES = {
    "晶体外壳": 1, "紫晶零件": 1, "紫晶质瓶": 2,
    "低容谷地电池": 16, "中容谷地电池": 30, "高容谷地电池": 70,
    "铁制零件": 1,
    "柑实罐头": 10, "优质柑实罐头": 27, "精选柑实罐头": 70,
    "荞愈胶囊": 10, "优质荞愈胶囊": 27, "精选荞愈胶囊": 70
}

# 1.3 发电数据
BASIC_GEN = 200 # 基地的基础发电量
POWER_DATA = {
    "Burn_Ore": ["源矿", 7.5, 50],
    "Burn_Bat_L": ["低容谷地电池", 1.5, 220],
    "Burn_Bat_M": ["中容谷地电池", 1.5, 420],
    "Burn_Bat_H": ["高容谷地电池", 1.5, 1100]
}
DEVICE_POWER = {
    "精炼炉": 5, "粉碎机": 5, "配件机": 10, "塑型机": 10,
    "灌装机": 20, "封装机": 20, "研磨机": 50,
    "种植组": 40 
}

# 1.4 据点类定义
class Stronghold:
    def __init__(self, name, rate, cap, items):
        self.name = name
        self.rate = rate
        self.cap = cap
        self.items = items

# ================= 2. Streamlit 界面构建 =================

st.set_page_config(page_title="产线规划器", layout="wide")
# --- 【新增】 侧边栏个人信息 ---
with st.sidebar:
    st.image("https://i.ibb.co/VcxWt4SJ/image.png", width=100)
    
    st.markdown("### 开发者信息")
    st.markdown("**圆锥**")
    st.markdown("就读于SJTU的本科2024级学生，热爱数学、机械和算法，梦想是成为~~像伊冯那样的~~深空机器人工程师，平时喜欢玩明日方舟、终末地、魂游等单机游戏。")
    
    # 社交链接
    st.markdown("""
    - 💻 [GitHub 主页](https://github.com/Cone-2540)
    - 🔗 [B站主页](https://space.bilibili.com/3493292419320630)
    - 📧 BUG反馈/联系邮箱: 1240368700@qq.com        
    - 🎮 终末地UID: 1899164058
    """)
    
    st.info("💡 **说明(Q&A)**：")
    st.markdown("1. 求解思路：基于Python的PuLP开源库中的**混合整数线性规划**算法和**二分查找**算法")
    st.markdown("2. 优化目标：如果产能充足，最大化玩家相邻上线时间间隔，使得可以一次性交易完所有据点的所有谷地调度券\
                ；如果产能不足，则最大化谷地调度券交易效率")
    st.markdown("3. 基建蓝图和毕业据点攻略在B站上已经很多，但是四号谷地的3个据点达到毕业之前仍有很长的游戏时间，\
                因此本网页更注重游戏过程，提供了任意非满级据点组合的最佳产线规划策略。")
    st.markdown("4. 得出对应产线产率需求后即可反推基建设备的布局，可以仿照生物代谢酶调控设计思路，关键中间产物回流\
                协议储存系统，用于其他非交易产物（如工业爆炸物、装备原件）制造")

st.title("🏭 《明日方舟：终末地》四号谷地工业产线规划器")

# --- 参数输入区域 ---
with st.container():
    st.subheader("🛠️ 核心参数设置")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**1. 据点配置 (据点等级/调度券产率/调度券上限)**")
        st.markdown("未来版本可能出现增加调度券上限的派驻干员能力，因此上限由手动输入，等级仅用于计算可交易物品")
        # 难民暂居处
        st.markdown("---")
        st.caption("难民暂居处")
        lv_refugee = st.number_input("难民暂居处等级 (0-4)", min_value=0, max_value=4, value=4, step=1)
        rate_refugee = st.number_input("难民暂居处产率", value=28107, step=100)
        cap_refugee = st.number_input("难民暂居处上限", value=2200000, step=10000)
        
        # 基建前站
        st.markdown("---")
        st.caption("基建前站")
        lv_outpost = st.number_input("基建前站等级 (0-4)", min_value=0, max_value=4, value=4, step=1)
        rate_outpost = st.number_input("基建前站产率", value=14820, step=100)
        cap_outpost = st.number_input("基建前站上限", value=680000, step=10000)
        
        # 重建指挥部
        st.markdown("---")
        st.caption("重建指挥部")
        lv_hq = st.number_input("重建指挥部等级 (0-4)", min_value=0, max_value=4, value=4, step=1)
        rate_hq = st.number_input("重建指挥部产率", value=20000, step=100)
        cap_hq = st.number_input("重建指挥部上限", value=1000000, step=10000)

    with col2:
        st.markdown("**2. 资源与全局**")
        storage_cap = st.number_input("仓库容量上限", value=14000, step=1000)
        power_redundancy = st.number_input("期望发电冗余（用于铺设滑索和防御塔等）", value=500, step=50)
        max_split_depth = st.number_input("分流器深度 (每个设备允许的分流器分流次数, 0为禁用分流器, 越深产线越灵活, 但是基建可读性越差且越复杂)", 0, 2, 0)
        
        st.markdown("**3. 矿产产能 (块/min)**")
        st.markdown("每个电驱矿机/二型电驱矿机均提供20矿/min")
        cap_ore = st.number_input("源矿产能", value=440, step=20)
        cap_amethyst = st.number_input("紫晶产能", value=220, step=20)
        cap_iron = st.number_input("蓝铁产能", value=300, step=20)
        
        MINING_CAPS = {"源矿": cap_ore, "紫晶": cap_amethyst, "蓝铁": cap_iron}

    with col3:
        st.markdown("**4. 作物解锁状态**")
        st.markdown("如果某个作物（如砂叶）未解锁，则相关的产线规划将自动屏蔽该作物的使用")
        use_buckwheat = st.checkbox("荞花", value=True)
        use_citrus = st.checkbox("柑实", value=True)
        use_sandleaf = st.checkbox("砂叶", value=False)
        
        UNLOCK_MASK = {
            "荞花": use_buckwheat,
            "柑实": use_citrus,
            "砂叶": use_sandleaf
        }
        
# ================= 3. 数据处理逻辑 =================

# 构造 Stronghold DB (带依赖逻辑)
STRONGHOLD_DB = {
    "难民暂居处": {
        "unlocks": {
            1: ["荞愈胶囊", "晶体外壳", "紫晶质瓶", "紫晶零件"],
            2: ["优质荞愈胶囊", "中容谷地电池", "柑实罐头"],
            3: ["高容谷地电池", "精选荞愈胶囊", "优质柑实罐头"],
            4: ["精选柑实罐头"]
        }
    },
    "基建前站": {
        "unlocks": {
            1: ["低容谷地电池", "铁制零件"],
            2: ["中容谷地电池", "优质荞愈胶囊"],
            3: ["高容谷地电池", "精选荞愈胶囊"],
            4: ["柑实罐头", "优质柑实罐头", "精选柑实罐头"]
        }
    },
    "重建指挥部": {
        "unlocks": {
            1: ["优质荞愈胶囊", "中容谷地电池", "铁制零件"],
            2: ["精选荞愈胶囊", "高容谷地电池"],
            3: ["柑实罐头", "优质柑实罐头", "精选柑实罐头"],
            4: [] 
        }
    }
}

# 动态生成 outlist
outlist = []
# 用户输入的参数映射
user_inputs = {
    "难民暂居处": {"lv": lv_refugee, "rate": rate_refugee, "cap": cap_refugee},
    "基建前站":   {"lv": lv_outpost, "rate": rate_outpost, "cap": cap_outpost},
    "重建指挥部": {"lv": lv_hq, "rate": rate_hq, "cap": cap_hq}
}

for name, params in user_inputs.items():
    level = params["lv"]
    rate = params["rate"]
    cap = params["cap"]
    
    if level > 0 and name in STRONGHOLD_DB:
        db_data = STRONGHOLD_DB[name]
        trade_items = []
        for l in range(1, level + 1):
            if l in db_data["unlocks"]:
                trade_items.extend(db_data["unlocks"][l])
        
        trade_items = list(set(trade_items))
        if trade_items:
            outlist.append(Stronghold(name, rate, cap, trade_items))

ALL_TRADEABLES = set(item for s in outlist for item in s.items)

# 生成分流配置
SPLIT_OPTIONS = {"Full": 1.0}
BASE_SPLITS = {"1/2": 0.5, "1/3": 1.0/3.0, "2/3": 2.0/3.0}
current_layer_splits = {"Full": 1.0}

for depth in range(1, max_split_depth + 1):
    next_layer_splits = {}
    for base_name, base_val in BASE_SPLITS.items():
        for parent_name, parent_val in current_layer_splits.items():
            new_val = parent_val * base_val
            # 简化命名逻辑
            found_simple_name = False
            for d in range(2, 20):
                for n in range(1, d):
                    if abs(n/d - new_val) < 0.0001:
                        new_name = f"{n}/{d}"
                        found_simple_name = True
                        break
                if found_simple_name: break
            
            if not found_simple_name:
                new_name = base_name if parent_name == "Full" else f"{parent_name}*{base_name}"
            
            is_duplicate = False
            for existing_name, existing_val in SPLIT_OPTIONS.items():
                if abs(existing_val - new_val) < 0.0001:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                SPLIT_OPTIONS[new_name] = new_val
                next_layer_splits[new_name] = new_val
    current_layer_splits = next_layer_splits

# ================= 4. 核心求解函数 (MILP) =================

def solve_production_milp(hours, mode='feasibility'):
    if mode == 'feasibility':
        prob = pulp.LpProblem(f"Plan_{hours}h_Feas", pulp.LpMinimize)
    else:
        prob = pulp.LpProblem(f"Plan_{hours}h_Max", pulp.LpMaximize)

    # 变量定义
    manufactured_items = df_recipes['产物名称'].unique()
    vars_machines = {}
    for item in manufactured_items:
        for label in SPLIT_OPTIONS:
            vars_machines[(item, label)] = pulp.LpVariable(f"Mach_{item}_{label}", lowBound=0, cat='Integer')

    vars_crops = {}
    for crop in UNLOCK_MASK:
        for label in SPLIT_OPTIONS:
            vars_crops[(crop, label)] = pulp.LpVariable(f"Crop_{crop}_{label}", lowBound=0, cat='Integer')

    vars_power = pulp.LpVariable.dicts("PowerSlot", POWER_DATA.keys(), lowBound=0, cat='Integer')

    alloc_vars = {}
    for s in outlist:
        for item in s.items:
            alloc_vars[(item, s.name)] = pulp.LpVariable(f"Alloc_{item}_{s.name}", lowBound=0)

    # 产出计算
    prod_rate_expr_map = {item: 0 for item in set(manufactured_items) | set(MINING_CAPS) | set(UNLOCK_MASK)}
    
    # 制造业产出
    for _, row in df_recipes.iterrows():
        item = row['产物名称']
        base_rate = (60.0 / row['加工时间秒']) * row['产物数量']
        total_item_prod = 0
        for label, ratio in SPLIT_OPTIONS.items():
            total_item_prod += vars_machines[(item, label)] * (base_rate * ratio)
        prod_rate_expr_map[item] = total_item_prod

    # 农业产出
    for crop in UNLOCK_MASK:
        base_rate = 30.0
        total_crop_prod = 0
        for label, ratio in SPLIT_OPTIONS.items():
            if not UNLOCK_MASK[crop]:
                prob += (vars_crops[(crop, label)] == 0, f"Lock_{crop}_{label}")
            total_crop_prod += vars_crops[(crop, label)] * (base_rate * ratio)
        prod_rate_expr_map[crop] = total_crop_prod

    # 消耗计算
    cons_rate_expr_map = {item: 0 for item in prod_rate_expr_map}
    
    for _, row in df_recipes.iterrows():
        for label, ratio in SPLIT_OPTIONS.items():
            cycles = vars_machines[(row['产物名称'], label)] * (60.0 / row['加工时间秒']) * ratio
            if row['原料1名称'] in cons_rate_expr_map:
                cons_rate_expr_map[row['原料1名称']] += cycles * row['原料1数量']
            if row['原料2名称'] and row['原料2名称'] in cons_rate_expr_map:
                cons_rate_expr_map[row['原料2名称']] += cycles * row['原料2数量']

    for code, data in POWER_DATA.items():
        cons_rate_expr_map[data[0]] += vars_power[code] * data[1]

    # 矿业闭环（产出=消耗）
    for m in MINING_CAPS:
        prod_rate_expr_map[m] = cons_rate_expr_map[m]

    # 约束条件
    # 1. 流量平衡
    all_involved = set(manufactured_items) | set(UNLOCK_MASK)
    net_rate_map = {}
    for item in all_involved:
        net_rate = prod_rate_expr_map[item] - cons_rate_expr_map[item]
        net_rate_map[item] = net_rate
        
        relevant_allocs = [alloc_vars[(item, s.name)] for s in outlist if (item, s.name) in alloc_vars]
        if relevant_allocs:
            total_check_alloc = pulp.lpSum(relevant_allocs)
            prob += (total_check_alloc <= net_rate * hours * 60, f"Accu_{item}")
            prob += (total_check_alloc <= storage_cap, f"Cap_{item}")
        else:
            prob += (net_rate >= -0.01, f"Balance_{item}")

    # 2. 矿产上限
    for m, cap in MINING_CAPS.items():
        prob += (cons_rate_expr_map[m] <= cap, f"Mining_Limit_{m}")

    # 3. 电力平衡
    total_gen = pulp.lpSum([vars_power[code] * data[2] for code, data in POWER_DATA.items()])
    total_load = 0
    # 矿机耗电
    total_load += (cons_rate_expr_map["源矿"] / 20 * 5) + (cons_rate_expr_map["紫晶"] / 20 * 5) + (cons_rate_expr_map["蓝铁"] / 20 * 10)
    # 农业耗电
    for crop in UNLOCK_MASK:
        for label in SPLIT_OPTIONS:
            total_load += vars_crops[(crop, label)] * DEVICE_POWER["种植组"]
    # 工业耗电
    for _, row in df_recipes.iterrows():
        base_power = DEVICE_POWER.get(row['设备名称'], 0)
        for label, ratio in SPLIT_OPTIONS.items():
            total_load += vars_machines[(row['产物名称'], label)] * base_power

    prob += (total_gen + BASIC_GEN >= total_load + power_redundancy, "Power")

    # 目标函数
    total_supplied_value = 0
    for s in outlist:
        demand = min(s.rate * hours, s.cap)
        supplied = pulp.lpSum([alloc_vars[(i, s.name)] * ITEM_PRICES.get(i, 0) for i in s.items])
        total_supplied_value += supplied
        
        if mode == 'feasibility':
            prob += (supplied >= demand - 0.1, f"Feas_{s.name}")
        else:
            prob += (supplied <= demand, f"Limit_{s.name}")

    if mode == 'feasibility':
        total_machine_count = pulp.lpSum(vars_machines.values()) + pulp.lpSum(vars_crops.values()) + pulp.lpSum(vars_power.values())
        prob += total_machine_count
    else:
        prob += total_supplied_value

    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return prob.status, net_rate_map, vars_machines, vars_crops, vars_power, alloc_vars, cons_rate_expr_map, total_gen, total_load


# ================= 5. 执行逻辑与结果展示 =================

st.markdown("---")
if st.button("开始规划计算", type="primary"):
    
    if not outlist:
        st.error("没有解锁任何据点或所有据点等级为0，请检查输入。")
    else:
        status_text = st.empty()
        status_text.info("正在搜索最优上线周期...")
        
        # 二分查找
        max_h = max([s.cap / s.rate for s in outlist]) + 0.5
        low, high = 0.1, max_h
        best_T = 0.0
        best_feasibility = False
        BINARY_SEARCH_STEP = 0.1

        while high - low > BINARY_SEARCH_STEP:
            mid = (low + high) / 2
            status, *others = solve_production_milp(mid, mode='feasibility')
            if status == pulp.LpStatusOptimal:
                best_T = mid
                low = mid
                best_feasibility = True
            else:
                high = mid
        
        final_T = best_T if best_feasibility else 1.0
        final_mode = 'feasibility' if best_feasibility else 'maximize'
        
        # 最终求解
        status_text.info(f"正在生成最终方案 (T={final_T:.2f}h)...")
        status, net_rates, v_mach, v_crop, v_pow, v_alloc, cons_map, expr_gen, expr_load = \
            solve_production_milp(final_T, mode=final_mode)
        
        status_text.empty()
        
        if status == pulp.LpStatusOptimal:
            st.success(f"规划完成！最大上线周期: {final_T:.1f} 小时 {'(产能饱和)' if not best_feasibility else ''}")
            
            # --- 1. 电力概览 ---
            st.header("⚡ 电力与资源概览")
            
            col_p1, col_p2, col_p3 = st.columns(3)
            val_gen = pulp.value(expr_gen) + BASIC_GEN
            val_load = pulp.value(expr_load)
            
            col_p1.metric("总发电量", f"{val_gen:.1f} ")
            col_p2.metric("总耗电量", f"{val_load:.1f} ", delta=f"负载率 {val_load/val_gen:.1%}", delta_color="inverse")
            col_p3.metric("电力盈余", f"{val_gen - val_load:.1f}", help=f"目标冗余 {power_redundancy}")
            
            # 矿物详情表
            mining_data = {
                "矿物类型": ["源矿", "紫晶", "蓝铁"],
                "开采量/min": [pulp.value(cons_map["源矿"]), pulp.value(cons_map["紫晶"]), pulp.value(cons_map["蓝铁"])],
                "上限/min": [MINING_CAPS["源矿"], MINING_CAPS["紫晶"], MINING_CAPS["蓝铁"]]
            }
            st.dataframe(pd.DataFrame(mining_data).style.format({"开采量/min": "{:.1f}", "上限/min": "{:.0f}"}), hide_index=True)

            # --- 2. 产线设备配置 ---
            st.header("⚙️ 制造与农业设备")
            
            machine_data = []
            
            # 工业
            for item in set(df_recipes['产物名称']):
                total_n = 0
                configs = []
                for label, ratio in SPLIT_OPTIONS.items():
                    n = int(pulp.value(v_mach[(item, label)]))
                    if n > 0:
                        total_n += n
                        configs.append(f"{n}x[{label}]")
                if total_n > 0:
                    net_out = pulp.value(net_rates[item])
                    machine_data.append({"类型": "制造", "名称": item, "数量": total_n, "配置详细": ", ".join(configs), "净产出/min": net_out})
            
            # 农业
            for crop in UNLOCK_MASK:
                total_n = 0
                configs = []
                for label, ratio in SPLIT_OPTIONS.items():
                    n = int(pulp.value(v_crop[(crop, label)]))
                    if n > 0:
                        total_n += n
                        configs.append(f"{n}x[{label}]")
                if total_n > 0:
                    machine_data.append({"类型": "农业", "名称": crop, "数量": total_n, "配置详细": ", ".join(configs), "净产出/min": 0})

            # 发电
            for code, var in v_pow.items():
                n = int(pulp.value(var))
                if n > 0:
                    machine_data.append({"类型": "发电", "名称": POWER_DATA[code][0], "数量": n, "配置详细": "全功率", "净产出/min": 0})
            
            df_res_mach = pd.DataFrame(machine_data)
            if not df_res_mach.empty:
                st.dataframe(df_res_mach.style.format({"净产出/min": "{:.2f}"}), hide_index=True, use_container_width=True)
            
            # --- 3. 交易策略 ---
            st.header("💰 交易分配")
            
            trade_rows = []
            for s in outlist:
                for item in s.items:
                    key = (item, s.name)
                    qty = pulp.value(v_alloc[key])
                    if qty and qty > 0.1:
                        val = qty * ITEM_PRICES.get(item, 0)
                        trade_rows.append({
                            "据点": s.name,
                            "物品": item,
                            "数量": int(qty),
                            "预估收益": int(val)
                        })
            
            if trade_rows:
                st.dataframe(pd.DataFrame(trade_rows), hide_index=True, use_container_width=True)
            else:
                st.info("无建议交易（可能全部用于内部循环或未达到最小起售量）")
        else:
            st.error("求解失败 (Infeasible)。请检查输入是否正确")
