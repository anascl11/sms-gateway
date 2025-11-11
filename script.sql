create database sms_gateway;

create user 'user'@'%' identified by 'password';
grant all privileges on sms_gateway.* to 'user'@'%';
flush privileges;

use sms_gateway;

create table users (
    id int auto_increment primary key,
    username varchar(50) not null unique,
    password varchar(255) not null,
    is_admin boolean default false,
    created_at datetime default current_timestamp
);

create table incoming_messages (
    id int auto_increment primary key,
    sender varchar(20) not null,
    message text not null,
    received_at datetime default current_timestamp
);

create table api_clients (
    id int auto_increment primary key,
    name varchar(50) not null unique,
    api_key varchar(255) not null unique,
    created_at datetime default current_timestamp
);

create table outgoing_messages (
    id int auto_increment primary key,
    receiver varchar(20) not null,
    message text not null,
    sent_at datetime default current_timestamp,
    user_id int null,
    api_client_id int null,
    foreign key (user_id) references users(id),
    foreign key (api_client_id) references api_clients(id)
);

