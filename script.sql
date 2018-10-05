CREATE SCHEMA IF NOT EXISTS `checker` DEFAULT CHARACTER SET utf8 ;
CREATE TABLE IF NOT EXISTS `checker`.`SNAPSHOTS` (
  `vm_name` VARCHAR(100) NOT NULL,
  `snap_name` VARCHAR(100) NOT NULL,
  `snap_size` VARCHAR(30) NOT NULL,
  `snap_time` DATETIME NOT NULL,
  `time` DATETIME NOT NULL)
ENGINE = InnoDB
DEFAULT CHARACTER SET = utf8;
create user 'check_user'@'localhost';
GRANT ALL PRIVILEGES ON checker.* TO 'check_user'@'localhost' WITH GRANT OPTION;
flush privileges;