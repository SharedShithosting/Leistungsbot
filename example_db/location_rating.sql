create table location_rating
(
    `key`    int auto_increment
        primary key,
    location int not null,
    member   int not null,
    rating   int not null,
    constraint location_rating_fk0
        foreign key (location) references locations (`key`),
    constraint location_rating_fk1
        foreign key (member) references members (`key`)
);

