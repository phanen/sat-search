## wtf
Use different SAT solvers to speed up differenial/linear cryptanalysis of `PRESENT` crypto.

sat solvers
* https://github.com/arminbiere/cadical
* https://github.com/msoos/cryptominisat
* https://github.com/arminbiere/kissat

sat optimizer
* https://github.com/hgarrereyn/SBVA

sources
* https://satcompetition.github.io/2023/downloads/satcomp23slides.pdf

## memo
线性分析: 部分线性式成立的 高概率/bias -> 构成区分器 (highly likely linear approximation)
* 堆积引理: 级联各 S 盒 bias 足够大 -> 整体较大的 bias (差的随机性)
* 概率成立的"线性性": 部分明文 bit, 部分最后一轮输入 bit = 部分中间轮 keys
  * keys 值对概率不确定, 但能确定 bias
* 已知明文攻击 (猜最后一轮相关的密钥)
  * 枚举可能的密钥 -> 对固定密钥, 统计到最后一轮前的明密文对的 bias 应符合预期值
* 寻找 active S-boxes
  * bias 越大 -> 整体线性式的 bias 量级越大 -> 构成的筛选器越强 -> 统计量成本越小
* 存在问题
  * 需要假设 each S-box approximation is independent -> 从而堆积引理适用 (现实: Sbox 可能不独立)
  * linear hull -> 相同起点和终点下, 我们估计的路径没有(覆盖)达到最大的 bias
  * 如果 linear bias 都很小, 区分能力太差, 不准确

差分分析: 差分输入输出式成立的 高概率 -> 构成区分器 (highly likely differential characteristics)
* 同样级联 S 盒等组件: 明文差分输入 -> 最后一轮差分输入
* 枚举关联 keys bits -> 对固定的 keys -> 统计差分匹配次数

引入 S 盒(非线性部件), 防止加密中出现确定性表达式 (非线性 -> 抵抗线性性 -> "防止加密被线性代数破解")
* 线性分析: Sbox 的输入 bits 和输入 bits 之间的线性关联 (线性分布表 lap)
* 差分分析: Sbox 的差分输入和差分输出之间的关联 (差分分布表 ddt)
* "线性安全": nonexistence of highly likely linear approximations(characteristics)
* "差分安全":  nonexistence of highly likely differential characteristics

如何搜索差分 trail
* MATSUI: branch-and-bound depth-first searching algorithm
* convert the Matsui’s bounding conditions into Boolean formulas (SAT problem)
  * not rely on new auxiliary variables and significantly reduces theconsumption of clauses
  * accelerating effect of the novel encoding methodunder different sets of bounding conditions
