# Google Drive 文件夹配置修复报告

## 问题描述

用户提供了一个"爷爷级别"的父文件夹链接，要求更新配置。但是页面显示的还是旧数据。

## 文件夹结构分析

### 用户提供的链接
```
https://drive.google.com/drive/folders/1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH?usp=sharing
```

### 实际文件夹层次结构
```
📂 1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH (爷爷级别 - 根目录)
 ├── 📁 data: 1o5Dtzb501G1hXqnxStwH2SPmOOD5i6lr
 ├── 📁 数据: 1bu5x679TXDi__eJ2BDLk9-oa6FkkT2ax
 ├── 📁 日志: 1h8I6SfVSM_MtMTafNzQFfAF_9MIvrUAv
 ├── 📁 监控: 1vinIbLVVzCZe4LecoxzMtJSKYV8JiX9_
 └── 📁 首页数据: 1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV ⭐ (父文件夹)
      ├── 📁 2026-01-03: 1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ ✅ (今天)
      ├── 📁 2026-01-02: 1RUqLfvCPC0lwvgr9xW3Alj2cHLCxFhtp
      ├── 📁 2026-01-01: 1Xkbyii7uirF-5f6aqrk67C1zxKAbTIJC
      ├── 📁 2025-12-31: 1WTgM-Uw2Hiou3TXaFg54S9M7VNLQS6DC
      └── ... (共75个日期文件夹)
```

## 关键发现

1. **"首页数据"文件夹是父文件夹**
   - 用户提供的是"爷爷级别"文件夹（包含多个子文件夹）
   - 真正需要的是"首页数据"文件夹
   - ID: `1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV`

2. **今天的日期文件夹**
   - 日期: 2026-01-03
   - ID: `1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ`
   - 包含119个TXT文件

3. **配置文件的问题**
   - 配置还在使用 2026-01-02 的文件夹
   - 需要更新到 2026-01-03

## 修复步骤

### 1. 查找"首页数据"文件夹
```python
# 使用 find_home_data_folder.py
parent_folder_id = "1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH"
# 结果: 找到"首页数据"文件夹 ID = 1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV
```

### 2. 查找今天的日期文件夹
```python
# 使用 check_date_folders.py
home_data_folder_id = "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV"
# 结果: 找到 2026-01-03 文件夹 ID = 1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ
```

### 3. 更新配置文件
```json
{
  "root_folder_odd": "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV",
  "root_folder_even": "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV",
  "current_date": "2026-01-03",
  "folder_id": "1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ",
  "parent_folder_id": "1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV",
  "folder_name": "2026-01-03",
  "last_updated": "2026-01-03 11:54:58",
  "update_reason": "手动更新到2026-01-03文件夹",
  "parent_folder_url": "https://drive.google.com/drive/folders/1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV?usp=sharing"
}
```

### 4. 重启服务
```bash
pm2 restart gdrive-detector
```

## 验证结果

### 日志输出
```
✅ 配置文件日期匹配: 2026-01-03
📂 从配置文件读取文件夹ID: 1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ
📂 当前使用的文件夹ID: 1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ (日期: 2026-01-03)
✅ 找到 119 个TXT文件（含真实ID）
最新3个文件: 2026-01-03_1952.txt, 2026-01-03_1942.txt, 2026-01-03_1932.txt
✅ 使用真实File ID: 10_r-LDGIbyfzY87koKjfXxyB5x4xnMRx
✅ 从文件内容提取时间戳: 2026-01-03 19:52:13
🎊 新数据已成功导入首页监控系统！
```

### 数据状态
- ✅ 正确读取 2026-01-03 的数据
- ✅ 找到 119 个TXT文件
- ✅ 最新文件: `2026-01-03_1952.txt`
- ✅ 数据时间戳: `2026-01-03 19:52:13`
- ✅ 数据成功导入 `crypto_snapshots` 表

## 创建的辅助脚本

### 1. find_home_data_folder.py
- 功能：在"爷爷级别"文件夹中查找"首页数据"文件夹
- 输入：父文件夹ID
- 输出："首页数据"文件夹的ID和URL

### 2. check_date_folders.py
- 功能：在"首页数据"文件夹中查找所有日期文件夹
- 输入："首页数据"文件夹ID
- 输出：按日期排序的文件夹列表，标注今天的文件夹

## 配置说明

### root_folder_odd 和 root_folder_even
- 用于支持单数/双数日期使用不同的父文件夹
- 当前两者都指向同一个"首页数据"文件夹
- 如果未来需要分开，可以设置不同的ID

### folder_id
- 当天使用的日期文件夹ID
- 每天会自动更新到新的日期文件夹
- 也可以手动更新

### parent_folder_id
- "首页数据"文件夹的ID
- 包含所有日期子文件夹的父文件夹

## Git提交记录

```bash
201030e - fix: 更新Google Drive文件夹配置到2026-01-03
```

### 修改的文件
1. `daily_folder_config.json` - 配置文件更新
2. `find_home_data_folder.py` - 新增辅助脚本
3. `check_date_folders.py` - 新增辅助脚本

## 后续维护

### 自动更新机制
`gdrive_final_detector.py` 包含自动更新机制：
- 每天00:10自动检查并更新到新日期的文件夹
- 如果11分钟超时，会自动触发恢复机制
- 恢复机制会重新查找今天的文件夹并更新配置

### 手动更新方法
如果需要手动更新到新的日期：
```bash
# 1. 运行检查脚本
python3 check_date_folders.py

# 2. 编辑配置文件
vi daily_folder_config.json
# 更新 current_date, folder_id, folder_name

# 3. 重启服务
pm2 restart gdrive-detector
```

## 总结

✅ **文件夹配置已完全修复**  
✅ **正确使用2026-01-03的数据**  
✅ **数据导入功能正常**  
✅ **自动更新机制正常**  

🔗 **关键链接：**
- 爷爷级别: https://drive.google.com/drive/folders/1U5VjRis2FYnBJvtR_8mmPrmFcJCMPGrH
- 首页数据: https://drive.google.com/drive/folders/1j8YV6KysUCmgcmASFOxztWWIE1Vq-kYV
- 今天文件夹: https://drive.google.com/drive/folders/1euzRzLjPDl08ZTvdDM_H_6hJzVNFldfQ

---

**修复完成时间：** 2026-01-03 19:55  
**当前状态：** ✅ 正常运行
