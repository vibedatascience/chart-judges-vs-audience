# 02 Clean

| step                                                                                                                    |   rows_remaining |   removed |
|:------------------------------------------------------------------------------------------------------------------------|-----------------:|----------:|
| raw rows                                                                                                                |            52836 |         0 |
| 1a. missing/unreadable image, missing score or date                                                                     |            52836 |         0 |
| 1b. blank image (grayscale std < 2.0)                                                                                   |            52688 |       148 |
| 2. chart type empty / none / Other                                                                                      |            46239 |      6449 |
| 3. short side < 300px                                                                                                   |            44433 |      1806 |
| 4. score < 5                                                                                                            |            35928 |      8505 |
| 5. near-duplicate (pHash Hamming <= 2): keep earliest; drop whole group if >= 3 posts with median title similarity < 60 |            34556 |      1372 |

- CSV rows whose image file was not found in the zips: 0
- Image files that failed to open: 0
- Duplicate groups with more than one post: 794
- Placeholder/template groups dropped entirely: 120 groups, 534 posts
- Multi-valued chart type rows kept in posts.parquet (excluded from pairing): 3014
- Single-type rows available for pairing: 31542
- Rows with no time of day: 5635

## Chart type (single-type rows)

| chart_type       |   posts |
|:-----------------|--------:|
| Bar              |    7554 |
| Maps             |    7041 |
| Line             |    6458 |
| Point            |    3561 |
| Diagrams         |    1505 |
| Grid & Matrix    |    1310 |
| Area             |    1303 |
| Trees & Networks |    1095 |
| Circle           |    1045 |
| Distribution     |     643 |
| Table            |      24 |
| Text             |       3 |

## Year

|   year |   posts |
|-------:|--------:|
|   2012 |     260 |
|   2013 |     863 |
|   2014 |    1434 |
|   2015 |    1335 |
|   2016 |    1780 |
|   2017 |    2999 |
|   2018 |    3852 |
|   2019 |    4311 |
|   2020 |    6437 |
|   2021 |    3977 |
|   2022 |    3452 |
|   2023 |    1733 |
|   2024 |    1954 |
|   2025 |     169 |
