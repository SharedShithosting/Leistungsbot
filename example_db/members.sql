create table members
(
    `key`   int auto_increment
        primary key,
    user_id bigint        not null,
    chat_id bigint        null,
    score   int default 0 not null,
    joined  datetime      not null,
    `left`  datetime      null,
    constraint chat_id
        unique (chat_id),
    constraint user_id
        unique (user_id)
);

INSERT INTO leistungs_db.members (`key`, user_id, chat_id, score, joined, `left`) VALUES (4, 4711, null, 0, '2022-10-13 19:50:14', null);
