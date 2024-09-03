create table leistungstag
(
    `key`    int auto_increment
        primary key,
    location int              not null,
    date     date             not null,
    poll_id  bigint           not null,
    venue_id bigint           not null,
    type     smallint         not null,
    closed   bit default b'0' not null,
    constraint leistungstag_fk0
        foreign key (location) references locations (`key`)
);

INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (1, 5, '2022-01-25', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (3, 6, '2022-02-01', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (5, 7, '2022-02-08', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (6, 8, '2022-02-15', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (7, 10, '2022-02-22', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (8, 11, '2022-03-01', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (9, 12, '2022-03-08', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (10, 13, '2022-03-15', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (11, 14, '2022-03-22', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (12, 15, '2022-03-29', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (13, 16, '2022-04-05', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (14, 17, '2022-04-12', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (15, 18, '2022-04-19', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (16, 19, '2022-04-26', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (17, 20, '2022-05-03', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (18, 21, '2022-05-10', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (19, 22, '2022-05-17', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (20, 23, '2022-05-24', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (21, 24, '2022-05-31', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (22, 26, '2022-06-07', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (23, 27, '2022-06-14', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (24, 28, '2022-06-21', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (25, 30, '2022-06-28', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (26, 31, '2022-07-05', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (27, 32, '2022-07-12', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (28, 33, '2022-07-19', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (29, 34, '2022-07-26', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (30, 36, '2022-08-02', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (31, 37, '2022-08-09', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (32, 38, '2022-08-16', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (33, 39, '2022-08-23', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (34, 40, '2022-08-30', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (35, 41, '2022-09-06', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (36, 42, '2022-09-13', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (37, 43, '2022-09-20', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (38, 44, '2022-09-27', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (39, 45, '2022-10-04', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (40, 46, '2022-10-11', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (44, 9, '2022-02-16', 0, 0, 3, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (45, 25, '2022-06-06', 0, 0, 3, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (46, 49, '2022-10-11', 0, 0, 2, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (47, 50, '2022-10-04', 0, 0, 2, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (49, 53, '2022-10-25', 732, 731, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (50, 56, '2022-11-01', 746, 745, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (51, 59, '2022-11-08', 753, 752, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (52, 61, '2022-11-15', 771, 770, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (54, 65, '2022-11-22', 796, 795, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (55, 29, '2022-06-24', 0, 0, 3, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (56, 47, '2022-10-18', 0, 0, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (57, 87, '2022-11-29', 830, 829, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (58, 90, '2022-12-06', 847, 846, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (59, 91, '2022-12-13', 862, 861, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (60, 92, '2022-12-20', 878, 877, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (61, 100, '2022-12-27', 899, 898, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (62, 98, '2023-01-03', 912, 911, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (63, 103, '2023-01-10', 936, 935, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (64, 13, '2023-01-17', 968, 967, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (65, 101, '2023-01-24', 970, 969, 1, true);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (66, 113, '2023-01-31', 980, 979, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (67, 114, '2023-02-07', 988, 987, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (68, 85, '2023-02-14', 1005, 1004, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (69, 125, '2023-02-21', 1012, 1011, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (70, 97, '2023-02-28', 1039, 1038, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (71, 127, '2023-03-07', 1056, 1055, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (72, 129, '2023-03-14', 1070, 1069, 1, false);
INSERT INTO leistungs_db.leistungstag (`key`, location, date, poll_id, venue_id, type, closed) VALUES (73, 84, '2023-03-21', 1099, 1098, 1, false);
