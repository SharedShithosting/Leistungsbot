# #############################################################################
#  "THE BEER-WARE LICENSE" (Revision 42):                                     #
#  @eckphi wrote this file. As long as you retain this notice you             #
#  can do whatever you want with this stuff. If we meet some day, and you think
#  this stuff is worth it, you can buy me a beer in return Poul-Henning Kamp  #
# #############################################################################
"""Handler mixins, one module per workflow.

Each class here is a slice of `LeistungsBot`, split out so a workflow
can be read on its own. They are mixins rather than standalone objects
because the handlers share the bot, the helper and the per user state;
untangling that shared state is the next step, and its own issue.
"""

from __future__ import annotations
