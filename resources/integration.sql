

-- API Description

insert into TBL_API_DESCRIPTION
(api_name, api_url, is_enabled, is_mocked, is_log_enabled, bypass_auth, api_description, mocked_response)
values ('find_parcel_list_by_centroid', '/parcels/find_parcel_list_by_centroid', 1, 1, 1, 0, '', '{"mocked": "true", "status": "OK"}');

insert into TBL_API_DESCRIPTION
(api_name, api_url, is_enabled, is_mocked, is_log_enabled, bypass_auth, api_description, mocked_response)
values ('find_parcel_info_by_centroid', '/parcels/find_parcel_info_by_centroid', 1, 0, 1, 0, '', '{"mocked": "true", "status": "OK"}');



-- channels

insert into TBL_CHANNEL (auth_key, channel_id, channel_name, description) VALUES
('123', '100', 'test', 'test channel');