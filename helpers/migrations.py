from helpers.mongodb import brick_all, brick_save, util_get, util_save
from helpers.shared import version_less_than, version_greater_or_equal_than
import copy


"""
Allways use the latest tagged version present in git when adding a new migrate from
this has the reason that you don't know for sure which version the current development will become
e.g. if the lateste version is 1.3.0 an your developing 1.4.X or 1.3.X create a migration as _migrate_from_130 and add it to the list as '1.3.0': _migrate_from_130
this migration is then executed when you publish e.g. the version 1.4.0 or 1.3.1 afterwards
"""


def _migrate_from_010():
    for brick in brick_all():
        if 'version' in brick:
            brick['features'] = copy.deepcopy(brick['version'])
            brick.pop('version')
        brick_save(brick)


_migrations = {
    '0.1.0': _migrate_from_010
}


def exec_migrate(current_version):
    last_migration = util_get('last_migration')
    if 'version' in last_migration:  # else a fresh installation is expected, so no need to migrate anything
        last_version = last_migration['version']
        print(f"Migrating from {last_version} to {current_version}")
        for v in sorted(_migrations.keys()):
            if version_greater_or_equal_than(v, last_version) and version_less_than(v, current_version):
                print(f"Executing migration: {v}")
                _migrations[v]()
    else:
        print("Fresh installation detected. No migrations needed!")
    last_migration['version'] = current_version
    util_save(last_migration)