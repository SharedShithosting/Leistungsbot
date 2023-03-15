create table participants
(
    `key`  int auto_increment
        primary key,
    member int not null,
    event  int not null,
    constraint participants_fk0
        foreign key (member) references members (`key`),
    constraint participants_fk1
        foreign key (event) references leistungstag (`key`)
);

INSERT INTO leistungs_db.participants (`key`, member, event) VALUES (1, 4, 1);
INSERT INTO leistungs_db.participants (`key`, member, event) VALUES (2, 4, 1);
INSERT INTO leistungs_db.participants (`key`, member, event) VALUES (3, 4, 1);
INSERT INTO leistungs_db.participants (`key`, member, event) VALUES (4, 4, 1);
