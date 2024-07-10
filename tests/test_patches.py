from pathlib import Path
from rimworld.mod import Mod, ModAbout
from rimworld.patch import apply_patches, collect_patches
from lxml import etree


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

    royalty = Mod(
            about = ModAbout(
                package_id='Ludeon.Rimworld.Royalty',
                author='Ludeon',
                supported_versions=[],
                ),
            path=Path('')
            )

    apply_patches(defs, collect_patches(patches), [royalty])
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

    royalty = Mod(
            about = ModAbout(
                package_id='Ludeon.Rimworld.Royalty',
                author='Ludeon',
                supported_versions=[],
                ),
            path=Path('')
            )

    apply_patches(defs, collect_patches(patches), [royalty])
    assert_xml_eq(defs, expected)


def test_patch_operation_find_mod():
    assert False


def assert_xml_eq(e1, e2, path=''):
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
        raise AssertionError(f"Number of children do not match at {path}: {len(e1)} != {len(e2)}")
    
    # Recursively compare children
    for i, (c1, c2) in enumerate(zip(e1, e2)):
        assert_xml_eq(c1, c2, path=f"{path}/{e1.tag}[{i}]")
