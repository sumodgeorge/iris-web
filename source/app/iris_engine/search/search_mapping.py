#!/usr/bin/env python3
#
#  IRIS Source Code
#  contact@dfir-iris.org
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
from app.models import AssetsType
from app.models.authorization import User
from app.models.cases import Cases
from app.models.models import CaseAssets

search_case_fields = {
    'case.id': Cases.case_id,
    'case.name': Cases.name,
    'case.description': Cases.description,
    'case.open_date': Cases.open_date,
    'case.close_date': Cases.close_date,
    'case.client_id': Cases.client_id,
    'case.soc_id': Cases.soc_id,
    'case.owner': User.user,
    'case.uuid': Cases.case_uuid,
    'case.custom_attributes': Cases.custom_attributes
}

search_asset_fields = {
    'asset.id': CaseAssets.asset_id,
    'asset.case_id': CaseAssets.case_id,
    'asset.type_name': AssetsType.asset_name,
    'asset.name': CaseAssets.asset_name,
    'asset.description': CaseAssets.asset_description,
    'asset.uuid': CaseAssets.asset_uuid,
    'asset.ip': CaseAssets.asset_ip,
    'asset.domain': CaseAssets.asset_domain,
    'asset.tags': CaseAssets.asset_tags,
    'asset.info': CaseAssets.asset_info,
    'asset.custom_attributes': CaseAssets.custom_attributes
}


search_fields = {}
search_fields.update(search_asset_fields)
search_fields.update(search_case_fields)

search_boolean_op = ['and', 'or']

search_separator = [':']