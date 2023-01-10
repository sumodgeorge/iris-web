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
import warnings

from sqlalchemy import and_
from sqlalchemy import or_

import app
from app import db
from app.iris_engine.search.search_mapping import search_fields
from app.iris_engine.search.search_mapping import search_separator

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

log = app.logger

class SearchParser(object):
    def __init__(self):
        self.has_warnings = False
        self.logs = []
        self.results = None
        self.has_errors = False
        self.tables = None
        self.entities = None

        # Inspired from pyparsing lucene example
        pp.ParserElement.enablePackrat()

        COLON, LBRACK, RBRACK, LBRACE, RBRACE, TILDE, CARAT = map(pp.Literal, ":[]{}~^")
        LPAR, RPAR = map(pp.Suppress, "()")
        and_, or_, not_, to_ = map(pp.CaselessKeyword, "AND OR NOT TO".split())
        keyword = and_ | or_ | not_ | to_

        expression = pp.Forward()

        valid_word = pp.Regex(
            r'([a-zA-Z0-9*_+.-]|\\\\|\\([+\-!(){}\[\]^"~*?:]|\|\||&&))+'
        ).setName("word")
        valid_word.setParseAction(
            lambda t: t[0].replace("\\\\", chr(127)).replace("\\", "").replace(chr(127), "\\")
        )

        string = pp.QuotedString('"')

        required_modifier = pp.Literal("+")("required")
        prohibit_modifier = pp.Literal("-")("prohibit")
        integer = ppc.integer()
        proximity_modifier = pp.Group(TILDE + integer("proximity"))
        number = ppc.fnumber()
        fuzzy_modifier = TILDE + pp.Optional(number, default=0.5)("fuzzy")

        term = pp.Forward().setName("field")
        field_name = valid_word().setName("fieldname")
        incl_range_search = pp.Group(LBRACK - term("lower") + to_ + term("upper") + RBRACK)
        excl_range_search = pp.Group(LBRACE - term("lower") + to_ + term("upper") + RBRACE)
        range_search = incl_range_search("incl_range") | excl_range_search("excl_range")
        boost = CARAT - number("boost")

        string_expr = pp.Group(string + proximity_modifier) | string
        word_expr = pp.Group(valid_word + fuzzy_modifier) | valid_word
        term << (
            ~keyword
            + pp.Optional(field_name("field") + COLON)
            + (word_expr | string_expr | range_search | pp.Group(LPAR + expression + RPAR))
            + pp.Optional(boost)
        )
        term.setParseAction(lambda t: [t] if "field" in t or "boost" in t else None)

        expression << pp.infixNotation(
            term,
            [
                (required_modifier | prohibit_modifier, 1, pp.opAssoc.RIGHT),
                ((not_ | "!").setParseAction(lambda: "NOT"), 1, pp.opAssoc.RIGHT),
                ((and_ | "&&").setParseAction(lambda: "AND"), 2, pp.opAssoc.LEFT),
                (
                    pp.Optional(or_ | "||").setName("or").setParseAction(lambda: "OR"),
                    2,
                    pp.opAssoc.LEFT,
                ),
            ],
        )

        self.parser = expression

    def parse(self, query):
        try:

            cpe = self.parser.parse_string(query)
            if not cpe[0]:
                return False

            scopes, query = self.parse_sub_expr(expr=cpe[0])
            logs = []

            if not scopes:
                return False

            joins, entities, tables, distinct = self.get_settings_from_scopes(scopes=scopes)

            with warnings.catch_warnings(record=True) as caught_warnings:

                if joins:
                    results = db.session.query(
                        *tables
                    ).with_entities(
                        *entities
                    ).filter(
                        query
                    ).join(
                        *joins
                    ).distinct(
                        *distinct
                    ).all()

                else:
                    results = db.session.query(
                        *tables
                    ).with_entities(
                        *entities
                    ).filter(
                        query
                    ).distinct(
                        *distinct
                    ).all()

                if caught_warnings:

                    if "Apply join condition" in str(caught_warnings[0].message):
                        logs = [
                            "Search query mixes incompatible fields, please refine your query. Search results may be incomplete."
                        ]
                        self.logs.extend(logs)
                    else:
                        logs = [str(w.message) for w in caught_warnings]
                        self.logs.extend(logs)
                    log.warning(f"Search query produced a warning: {caught_warnings[0].message}")

            self.logs = logs
            self.results = results
            self.has_warnings = True if logs else False
            self.tables = tables
            self.entities = list(results[0]._fields) if results else []

            return True

        except pp.ParseException as e:
            log.error("Error parsing query: %s", e)
            self.logs.append(f"Error parsing query: {e}")
            self.has_errors = True
            return False

        except Exception as e:
            log.error("Error parsing query: %s", e)
            self.logs.append(f"Error executing query.")
            self.has_errors = True
            return False

    def parse_sub_expr(self, expr):

        if len(expr) == 1 and isinstance(expr[0], pp.ParseResults):
            return self.parse_sub_expr(expr[0])

        if len(expr) != 3:
            log.error('Invalid expression. Expected term:value')
            self.logs.append('Invalid expression. Expected term:value')

            log.error(f'Got : {expr}')
            return None, None

        lterm = expr[0]
        operator = expr[1]
        rterm = expr[2]
        rterm_istr = True
        lterm_istr = True
        query_scope_1 = set()
        query_scope_2 = set()
        query_exp_2 = None
        query_exp_1 = None

        if type(lterm) is not str:
            lterm_istr = False
            query_scope_1, query_exp_1 = self.parse_sub_expr(expr=lterm)

        if type(rterm) is not str:
            rterm_istr = False
            query_scope_2, query_exp_2 = self.parse_sub_expr(expr=rterm)

        if operator in search_separator:
            if not lterm_istr:
                log.warning('Invalid expression. Field is not a string')
                self.logs.append('Invalid expression. Field is not a string.')
                return None, None

            if not rterm_istr:
                log.warning('Invalid expression. Value is not a string')
                self.logs.append('Invalid expression. Value is not a string.')
                return None, None

            term_scope = self.get_term_scope(lterm)
            if term_scope is None:
                log.warning(f'Unknown field type for {lterm}')
                self.logs.append(f'Unknown field type for {lterm}.')
                return None, None

            # build query part
            if "*" in rterm:
                query = term_scope['fields'][lterm].ilike(rterm.replace("*", "%"))
            else:
                query = term_scope['fields'][lterm] == rterm

            return {term_scope['scope']}, query

        else:
            if operator.lower() == 'and':
                if lterm_istr and rterm_istr:
                    log.warning('Invalid expression. Both terms are strings')
                    self.logs.append('Invalid expression. Both terms are strings.')
                    return None, None

                query = and_(query_exp_2, query_exp_1)

                return query_scope_1.union(query_scope_2), query

            elif operator.lower() == 'or':
                if lterm_istr and rterm_istr:
                    log.warning('Invalid expression. Both terms are strings')
                    self.logs.append('Invalid expression. Both terms are strings.')
                    return None, None

                query = or_(query_exp_2, query_exp_1)

                return query_scope_1.union(query_scope_2), query

    @staticmethod
    def get_term_scope(term: str):
        for scope in search_fields:
            if term in search_fields[scope]['fields']:
                return search_fields[scope]

        return None

    @staticmethod
    def get_settings_from_scopes(scopes: list):
        joins = set()
        entities = set()
        tables = set()
        distinct = set()

        for scope in scopes:
            joins.update(search_fields[scope]['joins'])
            entities.update(set(search_fields[scope]['entities']))
            tables.add(next(iter(search_fields[scope]['fields'].items()))[1].table)
            distinct.update(search_fields[scope]['distinct'])

        return joins, entities, tables, distinct
