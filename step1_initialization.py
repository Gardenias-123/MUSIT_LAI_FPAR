import os
import numpy as np
import rasterio
from tqdm import tqdm


def process_lai(lai_dir, qc_dir, output_dir):
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有LAI文件
    lai_files = [f for f in os.listdir(lai_dir) if f.startswith("COMP_LAI_5KM_") and f.endswith(".tif")]

    for lai_file in tqdm(lai_files, desc="Processing files"):
        try:
            # 解析日期部分
            date_part = lai_file.split("_")[-1].split(".")[0]

            # 构建QC文件路径
            qc_file = f"COMP_QC_5KM_{date_part}.tif"
            qc_path = os.path.join(qc_dir, qc_file)

            # 检查QC文件是否存在
            if not os.path.exists(qc_path):
                print(f"跳过 {lai_file}：缺少对应的QC文件")
                continue

            # 读取LAI数据
            with rasterio.open(os.path.join(lai_dir, lai_file)) as src:
                lai = src.read(1)
                meta = src.meta.copy()
                transform = src.transform
                crs = src.crs

            # 读取QC数据
            with rasterio.open(qc_path) as src:
                qc = src.read(1)

            # 计算平均值并填补
            mask = qc == 1
            mean_value = np.mean(lai)
            lai_filled = np.where(mask, mean_value, lai)

            # 转换为uint8并准备元数据
            lai_uint8 = lai_filled.astype(np.uint8)
            meta.update({
                'dtype': 'uint8',
                'compress': 'lzw',
                'driver': 'GTiff'
            })

            # 保存结果
            output_path = os.path.join(output_dir, f"LAI_STEP1_5KM_{date_part}.tif")
            with rasterio.open(output_path, 'w', **meta) as dst:
                dst.write(lai_uint8, 1)

        except Exception as e:
            print(f"处理 {lai_file} 时出错：{str(e)}")


if __name__ == "__main__":
    # 配置路径
    lai_directory = '../../COMP_5KM/COMP_LAI/'
    qc_directory = '../../COMP_5KM/COMP_QC/'
    output_directory = 'step1_output/'

    # 执行处理
    process_lai(lai_directory, qc_directory, output_directory)