delimiter //

create procedure `visualtables` ()
comment 'Create tables for visual app for dataronin'
begin

drop table if exists piedata;

create table piedata (
	`id` int unsigned not null auto_increment,
	`yy` int unsigned,
	`mm` int unsigned,
	`site` char(4),
	`tr` char(1),
	`pl` int unsigned,
	`rep` int unsigned,
	`den` int unsigned,
	`bio` int unsigned,
	`gro` int unsigned,
	`bir` int unsigned,
	`dea` int unsigned,
	primary key(`id`)
) engine=InnoDB;

load data infile 'C:/UniServer/django-projects/dataronin/visual/data/PIEdata.csv' 
into table piedata 
fields terminated by ',' 
ignore 1 lines
(`yy`, `mm`, `site`, `tr`, `pl`, `rep`, `den`, `bio`, `gro`, `bir`, `dea`);

drop table if exists kelp_grow_npp;

create table kelp_grow_npp (
	`id` int unsigned not null auto_increment,
	`site` char(4),
	`year` int unsigned,
	`season` varchar(10),
	`npp_wet` double,
	`npp_dry` double,
	`npp_carbon` double,
	`npp_nitrogen` double,
	`growth_rate_wet` double,
	`growth_rate_dry` double,
	`growth_rate_carbon` double,
	`growth_rate_nitrogen` double,
	`se_npp_wet` double,
	`se_npp_dry` double,
	`se_npp_carbon` double,
	`se_npp_nitrogen` double,
	`se_growth_rate_wet` double,
	`se_growth_rate_dry` double,
	`se_growth_rate_carbon` double,
	`se_growth_rate_nitrogen` double,
	primary key(`id`)
) engine=InnoDB;

load data infile 'C:/UniServer/django-projects/dataronin/visual/data/kelp_grow_npp.csv' 
into table kelp_grow_npp 
fields terminated by ','
ignore 1 lines
(`site`, `year`, `season`, `npp_wet`, `npp_dry`, `npp_carbon`, `npp_nitrogen`, `growth_rate_wet`, `growth_rate_dry`, `growth_rate_carbon`, `growth_rate_nitrogen`, `se_npp_wet`, `se_npp_dry`, `se_npp_carbon`, `se_npp_nitrogen`, `se_growth_rate_wet`, `se_growth_rate_dry`, `se_growth_rate_carbon`, `se_growth_rate_nitrogen`);

alter table kelp_grow_npp
add column `season_number` int unsigned
after `season`;

update kelp_grow_npp
set `season_number` = 2 where `season` = 'winter';

update kelp_grow_npp
set `season_number` = 5 where `season` = 'spring';

update kelp_grow_npp
set `season_number` = 8 where `season` = 'summer';

update kelp_grow_npp
set `season_number` = 11 where `season` = 'autumn';

drop table if exists hja_ws1_test;

create table hja_ws1_test (
	`id` int unsigned not null auto_increment,
	`plotid` int unsigned,
	`year` int unsigned,
	`bio_hw` double,
	`bio_all` double,
	`bio_con` double,
	`prop_bio_hw` double,
	`anpp` double,
	`basal_area_ha` double,
	`num_tree` int unsigned,
	`stem_den` double,
	`num_surv_assay` int unsigned,
	`bio_assay` double,
	`num_hw` int unsigned,
	`prop_hw_num` double,
	`stem_den_hw` double,
	`prop_hw_stem_den` double,
	primary key(`id`)
) engine=InnoDB;

load data infile 'C:/UniServer/django-projects/dataronin/visual/data/HJA_WS1_test.csv' 
into table hja_ws1_test 
fields terminated by ','
ignore 1 lines
(`plotid`, `year`, `bio_hw`, `bio_all`, `bio_con`, `prop_bio_hw`, `anpp`, `basal_area_ha`, `num_tree`, `stem_den`, `num_surv_assay`, `bio_assay`, `num_hw`, `prop_hw_num`, `stem_den_hw`, `prop_hw_stem_den`);

end //