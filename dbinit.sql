CREATE DATABASE flight_ticket_booking;

USE flight_ticket_booking;

CREATE TABLE `airplane` (
  `id` varchar(20) PRIMARY KEY,
  `seats` int,
  `airplane_model_id` int,
  `airliner_code` varchar(10)
);

CREATE TABLE `airliner` (
  `code` varchar(10) PRIMARY KEY,
  `name` varchar(50)
);

CREATE TABLE `manufacturer` (
  `id` int PRIMARY KEY,
  `name` varchar(30)
);

CREATE TABLE `airplane_model` (
  `id` int PRIMARY KEY,
  `name` varchar(50),
  `manufacturer_id` int
);

CREATE TABLE `airport` (
  `code` varchar(10) PRIMARY KEY,
  `name` varchar(50),
  `location` varchar(50)
);

CREATE TABLE `flight` (
  `id` varchar(20) PRIMARY KEY,
  `departure_on` datetime,
  `departure_airport_code` varchar(10),
  `stops` varchar(100),
  `duration` float,
  `arrival_airport_code` varchar(10),
  `airplane_id` varchar(20)
);

CREATE TABLE `fare` (
  `id` int PRIMARY KEY auto_increment,
  `flight_id` varchar(20),
  `total_seats` int,
  `tag` varchar(50),
  `description` varchar(100),
  `amount` float,
  `cancellation_fee` float,
  `max_cabin_bag_weight` int, 
  `max_baggage_weight` float
);

CREATE TABLE `user` (
  `email` varchar(50) primary key,
  `name` varchar(50),
  `phone` varchar(20),
  `password` varchar(255),
  `created_on` datetime default now()
);

CREATE TABLE `booking` (
  `id` int PRIMARY KEY auto_increment,
  `user_email` varchar(50),
  `fare_id` int,
  `booked_on` timestamp default now()
);

ALTER TABLE `airplane` ADD FOREIGN KEY (`airplane_model_id`) REFERENCES `airplane_model` (`id`);

ALTER TABLE `airplane` ADD FOREIGN KEY (`airliner_code`) REFERENCES `airliner` (`code`);

ALTER TABLE `airplane_model` ADD FOREIGN KEY (`manufacturer_id`) REFERENCES `manufacturer` (`id`);

ALTER TABLE `flight` ADD FOREIGN KEY (`departure_airport_code`) REFERENCES `airport` (`code`);

ALTER TABLE `flight` ADD FOREIGN KEY (`arrival_airport_code`) REFERENCES `airport` (`code`);

ALTER TABLE `flight` ADD FOREIGN KEY (`airplane_id`) REFERENCES `airplane` (`id`);

ALTER TABLE `fare` ADD FOREIGN KEY (`flight_id`) REFERENCES `flight` (`id`);

ALTER TABLE `booking` ADD FOREIGN KEY (`user_email`) REFERENCES `user` (`email`);

ALTER TABLE `booking` ADD FOREIGN KEY (`fare_id`) REFERENCES `fare` (`id`);

