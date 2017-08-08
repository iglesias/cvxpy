"""
Copyright 2013 Steven Diamond

This file is part of CVXPY.

CVXPY is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

CVXPY is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CVXPY.  If not, see <http://www.gnu.org/licenses/>.
"""

# Utility functions for constraints.

import cvxpy.lin_ops.lin_utils as lu
import scipy.sparse as sp


def format_axis(t, X, axis):
    """Formats all the row/column cones for the solver.

    Parameters
    ----------
        t: The scalar part of the second-order constraint.
        X: A matrix whose rows/columns are each a cone.
        axis: Slice by column 0 or row 1.

    Returns
    -------
    list
        A list of LinLeqConstr that represent all the elementwise cones.
    """
    # Reduce to norms of columns.
    if axis == 1:
        X = lu.transpose(X)
    # Create matrices Tmat, Xmat such that Tmat*t + Xmat*X
    # gives the format for the elementwise cone constraints.
    cone_size = 1 + X.shape[0]
    terms = []
    # Make t_mat
    mat_shape = (cone_size, 1)
    t_mat = sp.coo_matrix(([1.0], ([0], [0])), mat_shape).tocsc()
    t_mat = lu.create_const(t_mat, mat_shape, sparse=True)
    t_vec = t
    if not t.shape:
        # t is scalar
        t_vec = lu.reshape(t, (1, 1))
    else:
        # t is 1D
        t_vec = lu.reshape(t, (1, t.shape[0]))
    terms += [lu.mul_expr(t_mat, t_vec)]
    # Make X_mat
    mat_shape = (cone_size, X.shape[0])
    val_arr = (cone_size - 1)*[1.0]
    row_arr = range(1, cone_size)
    col_arr = range(cone_size-1)
    X_mat = sp.coo_matrix((val_arr, (row_arr, col_arr)), mat_shape).tocsc()
    X_mat = lu.create_const(X_mat, mat_shape, sparse=True)
    terms += [lu.mul_expr(X_mat, X)]
    return [lu.create_geq(lu.sum_expr(terms))]


def format_elemwise(vars_):
    """Formats all the elementwise cones for the solver.

    Parameters
    ----------
    vars_ : list
        A list of the LinOp expressions in the elementwise cones.

    Returns
    -------
    list
        A list of LinLeqConstr that represent all the elementwise cones.
    """
    # Create matrices Ai such that 0 <= A0*x0 + ... + An*xn
    # gives the format for the elementwise cone constraints.
    spacing = len(vars_)
    # Matrix spaces out columns of the LinOp expressions.
    mat_shape = (spacing*vars_[0].shape[0], vars_[0].shape[0])
    terms = []
    for i, var in enumerate(vars_):
        mat = get_spacing_matrix(mat_shape, spacing, i)
        terms.append(lu.mul_expr(mat, var))
    return [lu.create_geq(lu.sum_expr(terms))]


def get_spacing_matrix(shape, spacing, offset):
    """Returns a sparse matrix LinOp that spaces out an expression.

    Parameters
    ----------
    shape : tuple
        (rows in matrix, columns in matrix)
    spacing : int
        The number of rows between each non-zero.
    offset : int
        The number of zero rows at the beginning of the matrix.

    Returns
    -------
    LinOp
        A sparse matrix constant LinOp.
    """
    val_arr = []
    row_arr = []
    col_arr = []
    # Selects from each column.
    for var_row in range(shape[1]):
        val_arr.append(1.0)
        row_arr.append(spacing*var_row + offset)
        col_arr.append(var_row)
    mat = sp.coo_matrix((val_arr, (row_arr, col_arr)), shape).tocsc()
    return lu.create_const(mat, shape, sparse=True)
