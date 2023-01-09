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
from app.models import Client
from app.models.authorization import User
from app.models.cases import Cases
from app.models.models import CaseAssets

search_case_fields = {
    "scope": "case",
    "fields": {
        'case.id': Cases.case_id,
        'case.name': Cases.name,
        'case.description': Cases.description,
        'case.open_date': Cases.open_date,
        'case.close_date': Cases.close_date,
        'case.client_id': Cases.client_id,
        'case.client_name': Client.name,
        'case.soc_id': Cases.soc_id,
        'case.owner': User.user,
        'case.uuid': Cases.case_uuid,
        'case.custom_attributes': Cases.custom_attributes
    },
    "distinct": [Cases.case_id],
    "joins": [Cases.client, Cases.user],
    "entities": [
        Cases.case_id,
        Cases.name.label('case_name'),
        Cases.description.label('case_description'),
        Cases.open_date.label('case_open_date'),
        Cases.close_date.label('case_close_date'),
        Cases.client_id.label('case_client_id'),
        Cases.soc_id.label('case_soc_id'),
        Cases.case_uuid.label('case_uuid'),
        Cases.custom_attributes.label('case_custom_attributes'),
        Client.name.label('client_name'),
        User.user.label('case_owner')
    ]
}

search_asset_fields = {
    "scope": "asset",
    "fields": {
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
    },
    "distinct": [CaseAssets.asset_uuid],
    "joins": [CaseAssets.asset_type, CaseAssets.case],
    "entities": [
        CaseAssets.case_id,
        Cases.name.label('case_name'),
        CaseAssets.asset_id,
        CaseAssets.asset_name,
        CaseAssets.asset_description,
        CaseAssets.asset_uuid,
        CaseAssets.asset_ip,
        CaseAssets.asset_domain,
        CaseAssets.asset_tags,
        CaseAssets.asset_info,
        CaseAssets.custom_attributes.label('asset_custom_attributes'),
        AssetsType.asset_name.label('asset_type_name')
    ]
}


search_fields = {
    "case": search_case_fields,
    "asset": search_asset_fields
}

urls_mapping = {
    'case_id': '/case',
    'asset_id': '/case/assets'
}

search_boolean_op = ['and', 'or']

search_separator = [':']

def yield_search_fields():
    for scope in search_fields:
        for field in search_fields[scope]['fields']:
            yield field
