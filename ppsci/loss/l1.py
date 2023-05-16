# Copyright (c) 2023 PaddlePaddle Authors. All Rights Reserved.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict
from typing import Optional
from typing import Union

import paddle.nn.functional as F
from typing_extensions import Literal

from ppsci.loss import base


class L1Loss(base.Loss):
    r"""Class for l1 loss.

    $$
    L =
    \begin{cases}
        \dfrac{1}{N}\sum\limits_{i=1}^{N}{|x_i-y_i|}, & \text{if reduction='mean'} \\
        \sum\limits_{i=1}^{N}{|x_i-y_i|}, & \text{if reduction='sum'}
    \end{cases}
    $$

    Args:
        reduction (str, optional): Reduction method. Defaults to "mean".
        weight (Optional[Union[float, Dict[str, float]]]): Weight for loss. Defaults to None.

    Examples:
        >>> import ppsci
        >>> loss = ppsci.loss.L1Loss("mean")
    """

    def __init__(
        self,
        reduction: Literal["mean", "sum"] = "mean",
        weight: Optional[Union[float, Dict[str, float]]] = None,
    ):
        if reduction not in ["mean", "sum"]:
            raise ValueError(
                f"reduction should be 'mean' or 'sum', but got {reduction}"
            )
        super().__init__(reduction, weight)

    def forward(self, output_dict, label_dict, weight_dict=None):
        losses = 0.0
        for key in label_dict:
            loss = F.l1_loss(output_dict[key], label_dict[key], "none")
            if weight_dict is not None:
                loss *= weight_dict[key]
            if isinstance(self.weight, float):
                loss *= self.weight
            elif isinstance(self.weight, dict) and key in self.weight:
                loss *= self.weight[key]

            if "area" in output_dict:
                loss *= output_dict["area"]

            if self.reduction == "sum":
                loss = loss.sum()
            elif self.reduction == "mean":
                loss = loss.mean()

            if isinstance(self.weight, float):
                loss *= self.weight
            elif isinstance(self.weight, dict) and key in self.weight:
                loss *= self.weight[key]

            losses += loss
        return losses


class PeriodicL1Loss(base.Loss):
    """Class for periodic l1 loss.

    Args:
        reduction (str, optional): Reduction method. Defaults to "mean".
    """

    def __init__(
        self,
        reduction: Literal["mean", "sum"] = "mean",
        weight: Optional[Union[float, Dict[str, float]]] = None,
    ):
        if reduction not in ["mean", "sum"]:
            raise ValueError(
                f"reduction should be 'mean' or 'sum', but got {reduction}"
            )
        super().__init__(reduction, weight)

    def forward(self, output_dict, label_dict, weight_dict=None):
        losses = 0.0
        for key in label_dict:
            n_output = len(output_dict[key])
            if n_output % 2 > 0:
                raise ValueError(
                    f"Length of output({n_output}) of key({key}) should be even."
                )

            n_output //= 2
            loss = F.l1_loss(
                output_dict[key][:n_output], output_dict[key][n_output:], "none"
            )
            if weight_dict is not None:
                loss *= weight_dict[key]
            if "area" in output_dict:
                loss *= output_dict["area"]

            if self.reduction == "sum":
                loss = loss.sum()
            elif self.reduction == "mean":
                loss = loss.mean()

            if isinstance(self.weight, float):
                loss *= self.weight
            elif isinstance(self.weight, dict) and key in self.weight:
                loss *= self.weight[key]

            losses += loss
        return losses
