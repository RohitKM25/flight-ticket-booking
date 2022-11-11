CREATE DATABASE flight_ticket_booking;

USE flight_ticket_booking;

CREATE TABLE `airliner` (
  `code` varchar(10) PRIMARY KEY,
  `name` varchar(50),
  `location` varchar(50)
);

CREATE TABLE `airport` (
  `code` varchar(10) PRIMARY KEY,
  `name` varchar(50),
  `city ` varchar(50), 
  `region` varchar(50)
);

CREATE TABLE `flight` (
  `id` varchar(20) PRIMARY KEY,
  `departure_on` datetime,
  `departure_airport_code` varchar(10),
  `stops` varchar(100),
  `duration` float,
  `arrival_airport_code` varchar(10),
  `airplane_id` varchar(20),
  `airliner_code` varchar(10)
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