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
from flask import Blueprint
from flask import render_template
from flask import url_for
from flask_wtf import FlaskForm
from werkzeug.utils import redirect

from app.iris_engine.access_control.utils import ac_trace_case_access
from app.iris_engine.access_control.utils import ac_trace_effective_user_permissions
from app.iris_engine.access_control.utils import ac_trace_user_effective_cases_access
from app.models.authorization import Permissions
from app.util import ac_api_requires
from app.util import ac_requires
from app.util import response_success

manage_ac_blueprint = Blueprint(
        'access_control',
        __name__,
        template_folder='templates/access_control'
    )


@manage_ac_blueprint.route('/manage/access-control', methods=['GET'])
@ac_requires(Permissions.manage_users, Permissions.manage_own_organisation,
             Permissions.manage_groups, Permissions.manage_organisations, Permissions.read_users)
def manage_ac_index(caseid, url_redir):
    if url_redir:
        return redirect(url_for('access_control.manage_ac_index', cid=caseid))

    form = FlaskForm()

    return render_template("manage_access-control.html", form=form)


@manage_ac_blueprint.route('/manage/access-control/audit/users/<int:cur_id>', methods=['GET'])
@ac_api_requires(Permissions.manage_organisations)
def manage_ac_audit_user(cur_id, caseid):
    user_audit = {
        'access_audit': ac_trace_user_effective_cases_access(cur_id),
        'permissions_audit': ac_trace_effective_user_permissions(cur_id)
    }

    return response_success(data=user_audit)


@manage_ac_blueprint.route('/manage/access-control/audit/users/<int:cur_id>/modal', methods=['GET'])
@ac_api_requires(Permissions.manage_organisations)
def manage_ac_audit_user_modal(cur_id, caseid):
    access_audit = ac_trace_user_effective_cases_access(cur_id)
    permissions_audit = ac_trace_effective_user_permissions(cur_id)

    return render_template("modal_user_audit.html", access_audit=access_audit, permissions_audit=permissions_audit)


@manage_ac_blueprint.route('/manage/access-control/audit/users', methods=['GET'])
@ac_requires(Permissions.manage_organisations)
def manage_ac_audit_users_page(caseid, url_redir):
    form = FlaskForm()

    return render_template("manage_user_audit.html", form=form)


@manage_ac_blueprint.route('/manage/access-control/audit/cases', methods=['GET'])
@ac_requires(Permissions.manage_organisations)
def manage_ac_audit_cases_page(caseid, url_redir):
    form = FlaskForm()

    return render_template("manage_case_audit.html", form=form)


@manage_ac_blueprint.route('/manage/access-control/audit/cases/<int:cur_id>/modal', methods=['GET'])
@ac_api_requires(Permissions.manage_organisations)
def manage_ac_audit_cases_modal(cur_id, caseid):
    access_audit = ac_trace_case_access(cur_id)

    return render_template("modal_case_audit.html", access_audit=access_audit)


@manage_ac_blueprint.route('/manage/access-control/audit/cases/<int:cur_id>', methods=['GET'])
@ac_api_requires(Permissions.manage_organisations)
def manage_ac_audit_cases(cur_id, caseid):
    access_audit = ac_trace_case_access(cur_id)

    return response_success(data=access_audit)
