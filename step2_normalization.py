import os
import numpy as np
from osgeo import gdal
import glob
from tqdm import tqdm


def calculate_statistics(input_dir):
    """逐像素计算均值和标准差（内存优化版）"""
    files = sorted(glob.glob(os.path.join(input_dir, "LAI_STEP1_5KM_*.tif")))
    # 初始化统计变量
    ds = gdal.Open(files[0])
    H, W = ds.RasterYSize, ds.RasterXSize
    sum_ = np.zeros((H, W), dtype=np.float64)
    sum_sq = np.zeros((H, W), dtype=np.float64)
    count = np.zeros((H, W), dtype=np.int32)

    # 第一遍：计算总和
    for f in tqdm(files, desc="计算均值"):
        arr = gdal.Open(f).ReadAsArray().astype(np.float32)
    valid = (arr != 255)  # 假设255是填充值
    sum_ += np.where(valid, arr, 0)
    count += valid.astype(np.int32)

    mu = sum_ / np.maximum(count, 1)

    # 第二遍：计算标准差
    for f in tqdm(files, desc="计算标准差"):
        arr = gdal.Open(f).ReadAsArray().astype(np.float32)
    valid = (arr != 255)
    sum_sq += np.where(valid, (arr - mu) ** 2, 0)

    sigma = np.sqrt(sum_sq / np.maximum(count, 1))
    return mu, sigma


def normalize_single(input_path, output_dir, mu, sigma):
    """归一化单个文件"""
    ds = gdal.Open(input_path)
    arr = ds.ReadAsArray().astype(np.float32)
    valid = (arr != 255)

    # 归一化
    arr_norm = np.where(valid, (arr - mu) / sigma, 255)

    # 保存结果
    output_path = os.path.join(output_dir, os.path.basename(input_path).replace("STEP1", "STEP2"))
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_path, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Float32)
    out_ds.SetGeoTransform(ds.GetGeoTransform())
    out_ds.SetProjection(ds.GetProjection())
    out_ds.GetRasterBand(1).WriteArray(arr_norm)
    out_ds = None


if __name__ == "__main__":
    INPUT_DIR = "step1_output/"
    OUTPUT_DIR = "step2_output/"
    STATS_FILE = "norm_stats.npz"

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 计算统计量
    mu, sigma = calculate_statistics(INPUT_DIR)
    np.savez(STATS_FILE, mu=mu, sigma=sigma)

    # 归一化所有文件
    files = glob.glob(os.path.join(INPUT_DIR, "*.tif"))
    for f in tqdm(files, desc="归一化"):
        normalize_single(f, OUTPUT_DIR, mu, sigma)