


# Automeasurement
## Files

|File|Usage|
|:-|:-|
|./template/PLANT_PRM_TM_TEST_L_EXC.xml| Template file for all TM stages |
|./template/PLANT_PRM_IM_TEST_L_EXC.xml| Template file for all IM and MN stages |
|./template/PLANT_PRM_BF_TEST_L_EXC.xml| Template file for all BF stages with damper (not including Type-B)|
|./template/PLANT_ITMX_GAS_TEST_L_EXC.xml| Template file for all GAS chains|
|./template/PLANT_ITMX_IP_TEST_L_EXC.xml| Template file for all IP stages|

## For users

Case 1: Measure the TFs in IM stage for all Type-Bp and ITMX suspensions.
> python main.py -o PRM PR2 PR3 ITMX -s IM --runcp --rundiag

Case 2: Plot the TFs in IM stage for all Type-Bp suspensions.
> python main,py -o PRM PR2 PR3 -s BF --plot

## For developers


### AutoMeasurementの中身

まず指定された場所で励起するためのファイルをテンプレファイルから生成する。このファイルは一旦Archiveディレクトリに時間を末尾につけたファイル名として保存される。ファイルの実行はArchiveディレクトリ上で行われ、無事実行が終わればCurrentディレクトリにコピーされる。その際、ファイル名の末尾の日付は消しておく。


## Trouble shooting

 * If the measurement could not be started, please follow the explanation in error that you got.
