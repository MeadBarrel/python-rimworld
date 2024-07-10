from pathlib import Path
from rimworld.mod import Mod, ModAbout
from rimworld.patch import apply_patches, collect_patches
from lxml import etree


ROYALTY = Mod(
        about = ModAbout(
            package_id='Ludeon.Rimworld.Royalty',
            name='Royalty',
            author='Ludeon',
            supported_versions=[],
            ),
        path=Path('')
        )



RIMQUEST = Mod(
        about = ModAbout(
            package_id='rim_quest',
            name='RimQuest',
            author='Jecrell',
            supported_versions=[],
            ),
        path=Path('')
        )


def test_patch_operation_add():
    defs_xml = b'''<?xml version="1.0" encoding="utf-8"?>
    <Defs>
        <ThingDef>
            <defName>TSFApparel_SamuraiHelmet</defName>
            <recipeMaker>
                <recipeUsers>
                    <li>ElectricSmithy</li>
                    <li>FueledSmithy</li>
                </recipeUsers>
            </recipeMaker>
        </ThingDef>
        <ThingDef>
            <defName>TSFApparel_DaimyoHelmet</defName>
            <recipeMaker>
                <recipeUsers>
                    <li>ElectricSmithy</li>
                    <li>FueledSmithy</li>
                </recipeUsers>
            </recipeMaker>
        </ThingDef>
    </Defs>
    '''

    patch_xml = b'''<?xml version="1.0" encoding="utf-8"?>
    <Patch>
        <Operation Class="PatchOperationAdd">
            <xpath>Defs/ThingDef[defName="TSFApparel_SamuraiHelmet"]/recipeMaker/recipeUsers</xpath>
            <order>Prepend</order>
            <value>
                <li>DankPyon_Anvil</li>
            </value>
        </Operation>
        <Operation Class="PatchOperationAdd">
            <xpath>Defs/ThingDef[defName="TSFApparel_DaimyoHelmet"]/recipeMaker/recipeUsers</xpath>
            <value>
                <li>DankPyon_Anvil</li>
            </value>
        </Operation>
    </Patch>
    '''

    defs = etree.fromstring(defs_xml)
    patch = etree.fromstring(patch_xml)

    patches = collect_patches(patch)
    apply_patches(defs, patches)

    assert (
            defs.xpath(
                '/Defs/ThingDef[defName="TSFApparel_SamuraiHelmet"]/recipeMaker/recipeUsers/li/text()'
                )
            == ['DankPyon_Anvil', 'ElectricSmithy', 'FueledSmithy']
            )
    assert (
            defs.xpath(
                '/Defs/ThingDef[defName="TSFApparel_DaimyoHelmet"]/recipeMaker/recipeUsers/li/text()'
                )
            == ['ElectricSmithy', 'FueledSmithy', 'DankPyon_Anvil']
            )



def test_operation_add_append():
    defs = etree.fromstring('''
    <Defs>
        <ExampleDef>
          <defName>SampleDef</defName>
          <aaa>Some text</aaa>
        </ExampleDef>    
    </Defs>
    ''')
    patch = etree.fromstring('''
    <Defs>
        <Operation Class="PatchOperationAdd">
          <xpath>Defs/ExampleDef[defName="SampleDef"]</xpath>
          <value>
            <bbb>New text</bbb>
          </value>
        </Operation>                               
    </Defs>
    ''')
    expected = etree.fromstring('''
    <Defs>
        <ExampleDef>
          <defName>SampleDef</defName>
          <aaa>Some text</aaa>
          <bbb>New text</bbb>
        </ExampleDef>    
    </Defs>
    ''')
    apply_patches(defs, collect_patches(patch))
    assert_xml_eq(defs, expected)


def test_operation_insert_prepend():
    defs_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Rainbow</defName>
          <colors>
            <li>Red</li>
            <li>Yellow</li>
            <li>Green</li>
            <li>Blue</li>
            <li>Violet</li>
          </colors>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationInsert">
          <xpath>Defs/ExampleDef[defName="Rainbow"]/colors/li[text()="Yellow"]</xpath>
          <value>
            <li>Orange</li>
          </value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Rainbow</defName>
          <colors>
            <li>Red</li>
            <li>Orange</li>
            <li>Yellow</li>
            <li>Green</li>
            <li>Blue</li>
            <li>Violet</li>
          </colors>
        </ExampleDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_insert_append():
    defs_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Fish</defName>
          <lines>
            <li>one fish</li>
            <li>two fish</li>
          </lines>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationInsert">
          <xpath>Defs/ExampleDef[defName="Fish"]/lines/li[text()="two fish"]</xpath>
          <order>Append</order>
          <value>
            <li>red fish</li>
            <li>blue fish</li>
          </value>

        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Fish</defName>
          <lines>
            <li>one fish</li>
            <li>two fish</li>
            <li>red fish</li>
            <li>blue fish</li>
          </lines>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_remove():
    defs_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationRemove">
          <xpath>Defs/ExampleDef[defName="Sample"]/bar</xpath>
        </Operation>
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <baz>Tres</baz>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_replace():
    defs_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationReplace">
          <xpath>Defs/ExampleDef[defName="Sample"]/baz</xpath>
          <value>
            <baz>Drei</baz>
          </value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Drei</baz>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_attribute_add():
    defs_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationAttributeAdd">
          <xpath>Defs/ExampleDef[defName="Sample"]</xpath>
          <attribute>Name</attribute>
          <value>SampleBase</value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>

          <foo>Uno</foo>

          <bar>Dos</bar>

          <baz>Tres</baz>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_attribute_set():
    defs_xml = '''
    <Defs>
        <ExampleDef Name="SampleSource">
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationAttributeSet">
          <xpath>Defs/ExampleDef[defName="Sample"]</xpath>
          <attribute>Name</attribute>
          <value>SampleBase</value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>

          <foo>Uno</foo>

          <bar>Dos</bar>

          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_attribute_remove():
    defs_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>

          <foo>Uno</foo>

          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationAttributeRemove">
          <xpath>Defs/ExampleDef[defName="Sample"]</xpath>
          <attribute>Name</attribute>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef>
          <defName>Sample</defName>
          <foo>Uno</foo>
          <bar>Dos</bar>
          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_add_mod_extension():
    defs_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>
          <foo>Uno</foo>

          <bar>Dos</bar>

          <baz>Tres</baz>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationAddModExtension">

          <xpath>Defs/ExampleDef[defName="Sample"]</xpath>

          <value>
            <li Class="MyNamespace.MyModExtension">
              <key>Value</key>
            </li>
          </value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>

          <foo>Uno</foo>

          <bar>Dos</bar>
          <baz>Tres</baz>
          <modExtensions>

            <li Class="MyNamespace.MyModExtension">
              <key>Value</key>
            </li>
          </modExtensions>
        </ExampleDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_add_mod_extension_exists():
    defs_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>
          <foo>Uno</foo>

          <bar>Dos</bar>

          <baz>Tres</baz>

          <modExtensions>
            <li Class="Some.ModExtension">
              <key>Value1</key>
            </li>
          </modExtensions>
        </ExampleDef>    
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationAddModExtension">

          <xpath>Defs/ExampleDef[defName="Sample"]</xpath>

          <value>
            <li Class="MyNamespace.MyModExtension">
              <key>Value</key>
            </li>
          </value>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef Name="SampleBase">
          <defName>Sample</defName>

          <foo>Uno</foo>

          <bar>Dos</bar>
          <baz>Tres</baz>
          <modExtensions>

            <li Class="Some.ModExtension">
              <key>Value1</key>
            </li>

            <li Class="MyNamespace.MyModExtension">
              <key>Value</key>
            </li>
          </modExtensions>
        </ExampleDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_set_name():
    defs_xml = '''
    <Defs>
        <ThingDef>
          <defName>ExampleThing</defName>
          <!-- many nodes omitted -->
          <statBases>
            <Insulation_Cold>10</Insulation_Cold>
          </statBases>
        </ThingDef>
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationSetName">
          <xpath>Defs/ThingDef[defName="ExampleThing"]/statBases/Insulation_Cold</xpath>
          <name>Insulation_Heat</name>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ThingDef>
          <defName>ExampleThing</defName>
          <!-- many nodes omitted -->
          <statBases>
            <Insulation_Heat>10</Insulation_Heat>
          </statBases>
        </ThingDef>    
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_sequence():
    defs_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <Flammability>0.5</Flammability>
            </statBases>
        </ExampleDef>
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationSequence">
          <operations>
            <li Class="PatchOperationAdd">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases</xpath>
              <value>
                <Mass>10</Mass>
              </value>
            </li>
            <li Class="PatchOperationSetName">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases/Flammability</xpath>
              <name>ToxicEnvironmentResistance</name>
            </li>
          </operations>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <ToxicEnvironmentResistance>0.5</ToxicEnvironmentResistance>
                <Mass>10</Mass>
            </statBases>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def test_operation_sequence_may_require():
    defs_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <Flammability>0.5</Flammability>
            </statBases>
        </ExampleDef>
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationSequence">
          <operations>
            <li Class="PatchOperationAdd" MayRequire="Ludeon.Rimworld.Biotech">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases</xpath>
              <value>
                <Mass>10</Mass>
              </value>
            </li>
            <li Class="PatchOperationSetName" MayRequire="Ludeon.Rimworld.Royalty">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases/Flammability</xpath>
              <name>ToxicEnvironmentResistance</name>
            </li>
          </operations>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <ToxicEnvironmentResistance>0.5</ToxicEnvironmentResistance>
            </statBases>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches), [ROYALTY])
    assert_xml_eq(defs, expected)


def test_operation_sequence_may_require_any_of():
    defs_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <Flammability>0.5</Flammability>
            </statBases>
        </ExampleDef>
    </Defs>
    '''
    patches_xml = '''
    <Patch>
        <Operation Class="PatchOperationSequence">
          <operations>
            <li Class="PatchOperationAdd" MayRequireAnyOf="Ludeon.Rimworld.Biotech,MyMod.Me">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases</xpath>
              <value>
                <Mass>10</Mass>
              </value>
            </li>
            <li Class="PatchOperationSetName" MayRequireAnyOf="Ludeon.Rimworld.Royalty,Ludeon.Rimworld.Biotech">
              <xpath>Defs/ExampleDef[defName="Sample"]/statBases/Flammability</xpath>
              <name>ToxicEnvironmentResistance</name>
            </li>
          </operations>
        </Operation>    
    </Patch>
    '''

    expected_xml = '''
    <Defs>
        <ExampleDef> 
            <defName>Sample</defName>
            <statBases>
                <ToxicEnvironmentResistance>0.5</ToxicEnvironmentResistance>
            </statBases>
        </ExampleDef>
    </Defs>
    '''

    defs = etree.fromstring(defs_xml)
    patches = etree.fromstring(patches_xml)
    expected = etree.fromstring(expected_xml)

    apply_patches(defs, collect_patches(patches), [ROYALTY])
    assert_xml_eq(defs, expected)


def test_patch_operation_find_mod_match():
    defs = etree.fromstring('''
    <Defs>
        <IncidentDef>
            <defName>MFI_DiplomaticMarriage</defName>
        </IncidentDef>
        <IncidentDef>
            <defName>MFI_HuntersLodge</defName>
        </IncidentDef>
    </Defs>
    ''')

    patches = etree.fromstring('''
    <Patch>
        <Operation Class="PatchOperationFindMod">
          <mods>
            <li>RimQuest</li>
            <li>Royalty</li>
          </mods>

          <match Class="PatchOperationAddModExtension">
            <xpath>Defs/IncidentDef[defName="MFI_DiplomaticMarriage" or defName="MFI_HuntersLodge" or defName="MFI_Quest_PeaceTalks"]</xpath>

            <value>
              <li Class = "RimQuest.RimQuest_ModExtension">
                <canBeARimQuest>false</canBeARimQuest>
              </li>
            </value>

          </match>
        </Operation>
    </Patch>
    ''')

    expected = etree.fromstring('''
    <Defs>
        <IncidentDef>
            <defName>MFI_DiplomaticMarriage</defName>
            <modExtensions>
                <li Class="RimQuest.RimQuest_ModExtension">
                    <canBeARimQuest>false</canBeARimQuest>
                </li>
            </modExtensions>
        </IncidentDef>
        <IncidentDef>
            <defName>MFI_HuntersLodge</defName>
            <modExtensions>
                <li Class="RimQuest.RimQuest_ModExtension">
                    <canBeARimQuest>false</canBeARimQuest>
                </li>
            </modExtensions>
        </IncidentDef>
    </Defs>
    ''')

    apply_patches(defs, collect_patches(patches), mods=[RIMQUEST, ROYALTY])
    assert_xml_eq(defs, expected)


def test_patch_operation_find_mod_nomatch_do_nothing():
    defs_xml = '''
    <Defs>
        <IncidentDef>
            <defName>MFI_DiplomaticMarriage</defName>
        </IncidentDef>
        <IncidentDef>
            <defName>MFI_HuntersLodge</defName>
        </IncidentDef>
    </Defs>
    '''
    
    defs = etree.fromstring(defs_xml)
    expected = etree.fromstring(defs_xml)

    patches = etree.fromstring('''
    <Patch>
        <Operation Class="PatchOperationFindMod">
          <mods>
            <li>RimQuest</li>
            <li>Royalty</li>
          </mods>

          <match Class="PatchOperationAddModExtension">
            <xpath>Defs/IncidentDef[defName="MFI_DiplomaticMarriage" or defName="MFI_HuntersLodge" or defName="MFI_Quest_PeaceTalks"]</xpath>

            <value>

              <li Class = "RimQuest.RimQuest_ModExtension">
                <canBeARimQuest>false</canBeARimQuest>
              </li>
            </value>

          </match>
        </Operation>
    </Patch>
    ''')

    apply_patches(defs, collect_patches(patches), mods=[RIMQUEST])
    assert_xml_eq(defs, expected)


def test_patch_operation_find_mod_nomatch():
    defs = etree.fromstring('''
    <Defs>
        <IncidentDef>
            <defName>MFI_DiplomaticMarriage</defName>
        </IncidentDef>
        <IncidentDef>
            <defName>MFI_HuntersLodge</defName>
        </IncidentDef>
    </Defs>
    ''')

    patches = etree.fromstring('''
    <Patch>
        <Operation Class="PatchOperationFindMod">
          <mods>
            <li>RimQuest</li>
            <li>Royalty</li>
          </mods>

          <nomatch Class="PatchOperationAddModExtension">
            <xpath>Defs/IncidentDef[defName="MFI_DiplomaticMarriage" or defName="MFI_HuntersLodge" or defName="MFI_Quest_PeaceTalks"]</xpath>

            <value>

              <li Class = "RimQuest.RimQuest_ModExtension">
                <canBeARimQuest>false</canBeARimQuest>
              </li>
            </value>

          </nomatch>
        </Operation>
    </Patch>
    ''')

    expected = etree.fromstring('''
    <Defs>
        <IncidentDef>
            <defName>MFI_DiplomaticMarriage</defName>
            <modExtensions>
                <li Class="RimQuest.RimQuest_ModExtension">
                    <canBeARimQuest>false</canBeARimQuest>
                </li>
            </modExtensions>
        </IncidentDef>
        <IncidentDef>
            <defName>MFI_HuntersLodge</defName>
            <modExtensions>
                <li Class="RimQuest.RimQuest_ModExtension">
                    <canBeARimQuest>false</canBeARimQuest>
                </li>
            </modExtensions>
        </IncidentDef>
    </Defs>
    ''')

    apply_patches(defs, collect_patches(patches), mods=[RIMQUEST])
    assert_xml_eq(defs, expected)


def test_patch_operation_conditional_nomatch():
    defs = etree.fromstring('''
    <Defs>
        <WorldObjectDef>
            <defName>Caravan</defName>
        </WorldObjectDef>
    </Defs>
    ''')

    patches = etree.fromstring('''
    <Patch>
      <!-- add comps field to Caravan WorldObjectDef if it doesn't exist -->
      <Operation Class="PatchOperationConditional">
        <xpath>Defs/WorldObjectDef[defName="Caravan"]/comps</xpath>
        <nomatch Class="PatchOperationAdd">
          <xpath>Defs/WorldObjectDef[defName="Caravan"]</xpath>
          <value>
            <comps />

          </value>
        </nomatch>
      </Operation>
    </Patch>
    ''')

    expected = etree.fromstring('''
    <Defs>
        <WorldObjectDef>
            <defName>Caravan</defName>
            <comps />
        </WorldObjectDef>
    </Defs>
    ''')

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)

def test_patch_operation_conditional_match():
    defs = etree.fromstring('''
    <Defs>
        <WorldObjectDef>
            <defName>Caravan</defName>
            <blabla>hello</blabla>
        </WorldObjectDef>
    </Defs>
    ''')

    patches = etree.fromstring('''
    <Patch>
      <Operation Class="PatchOperationConditional">
        <xpath>Defs/WorldObjectDef[defName="Caravan"]/blabla</xpath>
        <match Class="PatchOperationAdd">
          <xpath>Defs/WorldObjectDef[defName="Caravan"]</xpath>
          <value>
            <comps />
          </value>
        </match>
      </Operation>
    </Patch>
    ''')

    expected = etree.fromstring('''
    <Defs>
        <WorldObjectDef>
            <defName>Caravan</defName>
            <blabla>hello</blabla>
            <comps />
        </WorldObjectDef>
    </Defs>
    ''')

    apply_patches(defs, collect_patches(patches))
    assert_xml_eq(defs, expected)


def assert_xml_eq(e1, e2, path=''):
    if not isinstance(e1, etree._Element):
        raise AssertionError(f'e1 ({e1}) is {type(e1)}, not _Element')
    if not isinstance(e2, etree._Element):
        raise AssertionError(f'e2 ({e2}) is {type(e2)}, not _Element')

    # Compare tags

    if e1.tag != e2.tag:
        raise AssertionError(f"Tags do not match at {path}: {e1.tag} != {e2.tag}")
    
    # Compare text
    if (e1.text or '').strip() != (e2.text or '').strip():
        raise AssertionError(f"Text does not match at {path}: '{e1.text}' != '{e2.text}'")
    
    # Compare tails
    if (e1.tail or '').strip() != (e2.tail or '').strip():

        raise AssertionError(f"Tails do not match at {path}: '{e1.tail}' != '{e2.tail}'")
    
    # Compare attributes
    if e1.attrib != e2.attrib:
        raise AssertionError(f"Attributes do not match at {path}: {e1.attrib} != {e2.attrib}")
    
    # Compare children
    if len(e1) != len(e2):
        print('NOMATCH')
        print(str(etree.tostring(e1, pretty_print=True)))
        print(str(etree.tostring(e2, pretty_print=True)))
        raise AssertionError(f"Number of children do not match at {path}: {len(e1)} != {len(e2)}")
    
    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(e1, e2)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")
