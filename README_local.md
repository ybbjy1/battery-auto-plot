# Electrochemical Auto Plot

一个基于 Streamlit 的电化学数据自动绘图网站，用于从 Excel/CSV 文件或网页输入参数生成论文风格图像。

## 功能

- Nyquist Plot：上传 EIS 数据，生成能奎斯特图。
- Arrhenius Plot：输入不同温度下的阻抗、样品厚度和面积，自动计算电导率并生成阿伦尼乌斯图。
- Rate Plot：上传倍率性能数据，生成倍率曲线。
- Cycling Plot：上传循环性能和库伦效率数据，生成循环曲线。

## 文件说明

```text
auto_plot_Internet/
├── app.py               # 网站总入口，部署时运行这个文件
├── Nyquist_plot.py      # 能奎斯特图功能
├── arrhenius_plot.py    # 阿伦尼乌斯图功能
├── Rate_plot.py         # 倍率曲线功能
├── Cycling_plot.py      # 循环曲线功能
├── requirements.txt     # Python 依赖
└── README.md            # 项目说明
```

## 本地运行

进入项目目录：

```bash
cd D:\Codexprojects\auto_plot_Internet
```

安装依赖：

```bash
pip install -r requirements.txt
```

启动网站：

```bash
streamlit run app.py
```

浏览器打开：

```text
http://127.0.0.1:8501
```

## 上传到互联网

### Streamlit Community Cloud

1. 将 `auto_plot_Internet` 文件夹中的全部文件上传到 GitHub 仓库。
2. 在 Streamlit Community Cloud 中新建应用。
3. 选择该 GitHub 仓库。
4. Main file path 填写：

```text
app.py
```

5. 部署时平台会自动读取 `requirements.txt` 安装依赖。

### 服务器部署

在服务器中安装 Python 后，执行：

```bash
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

然后通过服务器 IP 或域名访问对应端口。

## Excel 数据格式

### Nyquist Plot

推荐列名：

| 列名 | 含义 |
| --- | --- |
| series | 样品名称或图例分组 |
| x | Z' 或实部阻抗 |
| y | -Z'' 或虚部阻抗 |
| thickness | 电解质片厚度，单位 cm |
| area | 电解质片面积，单位 cm^2 |

也可以在网页端手动选择对应列。

### Rate Plot

推荐列名：

| 列名 | 含义 |
| --- | --- |
| series | 样品名称或图例分组 |
| cycle | 循环圈数 |
| capacity | 比容量 |
| rate_step | 倍率标签，可选 |

支持多组样品放在同一个 Sheet 中，通过 `series` 列区分。

### Cycling Plot

推荐列名：

| 列名 | 含义 |
| --- | --- |
| series | 样品名称或图例分组 |
| cycle | 循环圈数 |
| capacity | 比容量 |
| efficiency | 库伦效率 |

每个样品的容量曲线和库伦效率曲线会使用相同颜色，其中容量曲线进入图例，库伦效率曲线不进入图例。

## 输出图片

网页中预览图使用白色背景，下载的 PNG/PDF 按当前代码设置输出透明背景，适合后续插入论文或 PPT。

## 注意事项

- 推荐使用 `.xlsx` 文件。
- 如需读取旧版 `.xls` 文件，依赖中已包含 `xlrd`。
- 部署平台需要 Python 3.10 或更高版本。
- 如果部署后字体与本地略有差异，通常是服务器缺少 Arial 字体导致；可以在服务器安装 Arial 或接受 Matplotlib 的备用字体。
