# 01 Inventory

Source: beautiVis/beautiVis @ 739821c9703a6fa23f64895931b1ccc3a9238f2b, vis_csv.zip (156 monthly CSVs)

## Counts

| metric                                            | value   |
|:--------------------------------------------------|:--------|
| rows                                              | 52836   |
| unique pp_image_file                              | 52836   |
| image files found on disk                         | 0       |
| rows with image missing                           | 52836   |
| rows missing score                                | 0       |
| rows missing/unparseable created date             | 0       |
| missing expected columns                          | none    |
| rows with multi-valued gpt_overarching_chart_type | 3845    |
| rows with date but no time-of-day                 | 10744   |
| rows with score < 5                               | 10332   |

## Posts per year

|   year |   posts |   no_time |   median |    p90 |
|-------:|--------:|----------:|---------:|-------:|
|   2012 |     463 |         0 |     45   |  328.6 |
|   2013 |    1354 |         0 |     29   |  839.3 |
|   2014 |    2493 |      2493 |     15   | 1043   |
|   2015 |    3273 |      2981 |      6   |  172.4 |
|   2016 |    3569 |         0 |     10   |  258.8 |
|   2017 |    4743 |         0 |     16   |  356   |
|   2018 |    5693 |         0 |     18   |  490.4 |
|   2019 |    5951 |         0 |     22   |  922   |
|   2020 |    8984 |         0 |     27   |  704.5 |
|   2021 |    5137 |         0 |     52   | 6657.8 |
|   2022 |    4718 |         0 |     64.5 | 7649.9 |
|   2023 |    3225 |      2037 |     26   | 2682.4 |
|   2024 |    2979 |      2979 |    102   | 1834.6 |
|   2025 |     254 |       254 |     83.5 | 1200.2 |

## Posts per gpt_overarching_chart_type (raw string, top 30)

| type                |   posts |
|:--------------------|--------:|
| Bar                 |   10136 |
| Maps                |    9304 |
| Line                |    8936 |
| (empty)             |    5626 |
| Point               |    4872 |
| Diagrams            |    1938 |
| Area                |    1770 |
| Grid & Matrix       |    1704 |
| Trees & Networks    |    1520 |
| Circle              |    1466 |
| Bar, Line           |     919 |
| Other               |     857 |
| Distribution        |     826 |
| Bar, Circle         |     333 |
| Point, Line         |     261 |
| Bar, Maps           |     226 |
| Area, Line          |     175 |
| Point, Maps         |     169 |
| Point, Bar          |     167 |
| Maps, Line          |     155 |
| Maps, Bar           |      80 |
| Maps, Circle        |      73 |
| Area, Bar           |      73 |
| Distribution, Point |      60 |
| Distribution, Line  |      53 |
| Grid & Matrix, Line |      50 |
| Circle, Line        |      49 |
| Circle, Bar, Line   |      44 |
| Distribution, Maps  |      43 |
| Area, Maps          |      42 |

221 distinct raw values in total.

## Posts per primary type (first listed category)

| primary_type     |   posts |
|:-----------------|--------:|
| Bar              |   11735 |
| Maps             |    9684 |
| Line             |    9018 |
| (empty)          |    5626 |
| Point            |    5570 |
| Area             |    2197 |
| Diagrams         |    1994 |
| Grid & Matrix    |    1827 |
| Circle           |    1581 |
| Trees & Networks |    1532 |
| Distribution     |    1124 |
| Other            |     905 |
| Table            |      38 |
| Text             |       5 |

## Score quantiles

|   quantile |    score |
|-----------:|---------:|
|       0    |      0   |
|       0.1  |      1   |
|       0.25 |      7   |
|       0.5  |     23   |
|       0.75 |    115   |
|       0.9  |   1482   |
|       0.99 |  32204.3 |
|       1    | 162617   |

## 10 sample rows (seed 20261008)

| pp_image_file    | json_created_date   |   json_score |   json_num_comments | gpt_overarching_chart_type   | json_title                                                                       |
|:-----------------|:--------------------|-------------:|--------------------:|:-----------------------------|:---------------------------------------------------------------------------------|
| 2019-07-0135.png | 2019-07-10 15:58:32 |           18 |                  11 | Line                         | The relationship between Stranger Things and Planck's constant Google searches o |
| 2022-01-0410.png | 2022-01-26 01:24:40 |          127 |                  54 | Distribution                 | [OC] Board game ratings among popular game series/themes                         |
| 2020-01-0332.png | 2020-01-13 08:48:19 |           12 |                   4 | Grid & Matrix                | [OC] Ground elevation of Caucasus measured by the NASA SRTM mission (the brighte |
| 2021-12-0115.png | 2021-12-09 18:29:17 |           22 |                   6 | Point                        | [OC] Deaths in conflicts around the world vs Reddit comments - end of the year e |
| 2017-09-0421.jpg | 2017-09-26 18:02:44 |           34 |                   5 | Grid & Matrix                | A Heatmap of Counter-Strike Player's Positioning over 1000 recorded Matchmaking  |
| 2021-06-0221.png | 2021-06-15 15:14:35 |           56 |                  47 | Bar                          | [OC] Environmental Impact of Coffee Brewing Methods                              |
| 2019-08-0321.png | 2019-08-20 22:23:38 |           44 |                  14 | Area                         | [OC] Net Generation by State and Energy Source, 1990-2017                        |
| 2021-08-0382.jpg | 2021-08-28 18:08:47 |          154 |                  22 | Bar                          | COVID Deaths since June '21 by states' vaccination [OC]                          |
| 2020-10-0478.png | 2020-10-23 22:22:35 |          175 |                  68 | Bar                          | [OC] Fun fact: 19 of 58 US Presidents (39%) haven't been elected with a majority |
| 2021-12-0316.jpg | 2021-12-24 14:43:06 |           90 |                  29 |                              | Visualizing the $94 Trillion World Economy in One Chart                          |
