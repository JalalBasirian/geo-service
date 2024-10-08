from py.service.parcel_service import *
# from util.gis_util import transform_point
from common.constants import UTM_ZONE_38_SRID
from gis.model.models import Point_T
from .common import handle_response
from util.common_util import get_state_code_by_name
from model.dto.ParcelDTO import *


from fastapi import APIRouter, Request
from dispatcher.dispatcher import dispatch

router = APIRouter()


@router.get("/find_polygon_by_centroid")
@dispatch
def find_polygon_by_centroid_api(request: Request, longtitude: float, latitude: float, srid="4326"):
    """
        lat/lon CRS is 4326
    """

    point = Point_T(longtitude, latitude, srid)
    # if srid != "4326":
    #     point = transform_point(point, "4326")
    geometry_wkt = find_polygon_by_centroid(point)

    return handle_response({"parcel": str(geometry_wkt)})


@router.get("/find_parcel_info_by_centroid")
@dispatch
def find_parcel_info_by_centroid_api(request: Request, longtitude: float, latitude: float, srid="4326"):
    point = Point_T(longtitude, latitude, srid)
    parcel = find_parcel_info_by_centroid(point)
    parcel_info = assemble_parcel_info_response(parcel)
    response = ParcelInfoResponse(parcel_info)
    return handle_response(response)


def assemble_parcel_info_response(parcel) -> ParcelInfoDTO:
    deed = parcel.deed
    state = deed.state
    state_code = get_state_code_by_name(state)

    apartments = []

    if deed.deed_parts:
        for part in deed.deed_parts:
            apartment_metadata = ParcelMetadataDTO(subsidiary_plate_number=part.subsidiary_plate_number,
                                                partitioned=deed.partitioned,
                                                segment=deed.segment,
                                                area=deed.legal_area)
            apartments.append(apartment_metadata)

    common_metadata = ParcelMetadataDTO(state=state,
                                        state_code=state_code,
                                        cms=deed.cms,
                                        section=deed.section,
                                        district=deed.district,
                                        main_plate_number=deed.main_plate_number)

    parcel_geom = ParcelGeomDTO(geom=str(parcel.polygon),
                                type="POLYGON",  # TODO: static value for now, but should be dynamic later
                                crs="ESPG:4326"  # TODO: static value for now, but should be dynamic later
                                )

    ground_metadata = ParcelMetadataDTO(subsidiary_plate_number=deed.subsidiary_plate_number,
                                        partitioned=deed.partitioned,
                                        segment=deed.segment,
                                        area="TODO")

    parcel_ground = ParcelGroundDTO(parcel_geom=parcel_geom,
                                    metadata=ground_metadata)

    parcel_info = ParcelInfoDTO(common_metadata=common_metadata,
                                ground=parcel_ground,
                                apartments=apartments)

    return parcel_info