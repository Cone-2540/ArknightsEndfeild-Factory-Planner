# 🏭 Endfield Industry Planner (明日方舟终末地工业规划器)

这是一个基于 MILP (混合整数线性规划) 算法的明日方舟终末地产线自动化规划工具。
由 **圆锥** 开发。

## 🧮 算法流程

```mermaid
graph TD
    subgraph "User Interface (Streamlit)"
        Input[用户参数输入] -->|据点状态/产能/电力冗余| Config
        Param[游戏静态数据] -->|配方/能耗/价格| Config
    end

    subgraph "Core Logic (Python)"
        Config --> PreProcess[预处理: 生成需求清单 & 分流比例]
        PreProcess --> Loop{二分查找最优周期 T}
        
        Loop -->|尝试时间 T| Solver
        
        subgraph "Solver (PuLP MILP)"
            DefVar["定义变量:机器数(Int), 流量(Float)"]
            Constraint1[约束1: 物质守恒 & 供需平衡]
            Constraint2[约束2: 电力平衡 > 负载+冗余]
            Constraint3[约束3: 矿产开采 < 上限]
            
            DefVar --> Constraint1
            DefVar --> Constraint2
            DefVar --> Constraint3
            Constraint3 --> Objective[目标: 可行性 & 最小化设施]
        end
        
        Objective -->|返回状态| Loop
    end

    Loop -->|找到最佳方案| Parser[结果解析]
    Parser --> Output[生成: 建造清单/电力报表/交易策略]
    Output --> Display((网页展示))

    style Solver fill:#f9f,stroke:#333,stroke-width:2px
    style Input fill:#aaf,stroke:#333,stroke-width:2px
    style Display fill:#9f9,stroke:#333,stroke-width:2px
```

## 🛠️ 功能特点
- **自动规划**：基于目标产能，自动计算最优设备配比。
- **电力平衡**：自动计算总耗电与发电设备需求。
- **收益最大化**：使用线性规划求解器 (PuLP) 计算单位时间最大收益。

## 📦 技术栈
- Python 3.9+
- Streamlit (Web UI)
- Pandas & PuLP (算法求解)

## 🚀 在线运行
点击下方链接直接使用（无需安装）：
[Planner](https://atbzigcbev2hyy7kwwhjhl.streamlit.app/)

## 💻 本地运行
```bash
pip install -r requirements.txt
streamlit run EndfeildPlanner.py
