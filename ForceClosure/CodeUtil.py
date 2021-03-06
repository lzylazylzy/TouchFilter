import os
import numpy as np
import torch
import torch.nn as nn
import trimesh

# np.random.seed(0)
# torch.manual_seed(0)

code_path = 'data/Reconstructions/2000/Codes/ShapeNetCore.v2/02876657'
mesh_path = 'data/Reconstructions/2000/Meshes/ShapeNetCore.v2/02876657'

_codes = []
_meshes = []
_fns = os.listdir(code_path)

skip = [
  '134c723696216addedee8d59893c8633.pth', 
  '74221bae887b0e801ab89e10ca4a3aec.pth',
  '7446fa250adf49c5e7ef9fff09638f8e.pth', 
  '495dea92a04b43e6be9fabb33de62010.pth', 
  '518f6867e5d38301fd3bf7a5792372cb.pth', 
  '5277b4491396a522333769b054e66b40.pth', 
  'b31ca446cb3e88dda88e473ddd1152a6.pth', 
  'b45d6cadaba5b6a72d20e9f11baa5f8f.pth', 
  'b6261066a2e8e4212c528d33bca1ac2.pth', 
  'ba4b48d76eb79f7cf54e1b6f41fdd78a.pth', 
  '5c1253ae61a16e306871591246ec74dc.pth', 
  'd511899945a400b183b4ef314c5735aa.pth', 
  'd5dd0b4d16d2b6808bda158eedb63a62.pth', 
  'd74bc917899133e080c257afea181fa2.pth',
  'd851cbc873de1c4d3b6eb309177a6753.pth',
  'd85f1862dfe799cbf78b6c51ab8f145e.pth', 
  '1f1e747bfce16fe0589ac2c115a083f1.pth',
  '5ac30e855ea3faad8884a069d9619eaf.pth', 
  '6444875e3217bf891f5f48a891d827bd.pth',
  '77ad88568cb55237e01d7dc978602402.pth',
  '92472817f72dd619467ca2ad6571afff.pth',
  '99d595bf3ac08bace13f76b539e1d69a.pth',
  '9ba6291a60113dbfeb6d856318cd1a7e.pth',
  '2efb9eef0ed832a89769b3a50399d097.pth',
  '3108a736282eec1bc58e834f0b160845.pth',
  'e7818a94d20fd8e1a4136492f17b9a59.pth',
  'edfcffbdd585d00ec41b4a535d52e063.pth',
  'f03f9704001d2055ab8a56962d772d13.pth',
  'f1ae9b2eb551ba466dc523ea4bf73f1c.pth',
  'f1c0e107dc158727a8360f05ea0a1d2d.pth',
  'a4a6a464cb1db9286bdbc69440dbff90.pth',
  'ab5ca2f648a9daa1b5ad628041310f96.pth',
  '829ad86e645d11b1bcbe24a1993b1795.pth',
  '84bc4006535545fad2986c98896facaa.pth',
  '8a0320b2be22e234d0d131ea6d955bf0.pth',
  '645cf2b7f442865ebf8d8d6022c8e3a.pth',
  '64faa2a6a6f844af851f4ba6aaedaaa8.pth',
  '6821f9cc313dfdebe7ef9fff09638f8e.pth',
  '6987e839b802a349a9039b9668d0f11f.pth',
  '6a96b74beea7f5b316aa41fc58452f78.pth',
  '6ab0ef1973477031ad5067eac75a07f7.pth',
  '6c56bd467b8e6b7912c4d7e462c15a1a.pth',
  '3ba7dd61736e7a96270c0e719fe4ed97.pth',
  '3d758f0c11f01e3e3ddcd369aa279f39.pth',
  'c6442bba98ad3dcf5e912b2d2934c0b6.pth',
  'c80173e23efaac35535deb3b0c692a2a.pth',
  'c82bbd1b1a929c7ce8ed8cf0a077ddf7.pth',
  'cbc1cbc9cf65e9c2fd1d6016d24cc8d.pth',
  'cf6eff1143f9826ab5c14191b5dd293b.pth',
  'd297d1b0e4f0c244f61150ce90be197a.pth',
  'd2c9c369376827adf8f0533aaf004c87.pth',
  'd2e7e725aa6b39f0d333084c1357713e.pth',
  '546111e6869f41aca577e3e5353dd356.pth',
  '546eded3ac7801412389a54fb53b0765.pth',
  '547fa0085800c5c3846564a8a219239b.pth',
  '591153135f8571a69fc36bc06f1db2fa.pth',
  '200b3f3d859c8677ad5067eac75a07f7.pth',
  '204c2b0a5e0a0ac3efd4121045846f28.pth',
  '216adefa94f25d7968a3710932407607.pth',
  '225d046d8f798afacba9caf4d254cef0.pth',
  '244894af3ba967ccd957eaf7f4edb205.pth',
  'f853ac62bc288e48e56a63d21fb60ae9.pth',
  'fa452996a220dd49257c84a0e95a18b0.pth',
  'ffa6c49aa8f7ec19971e7f8dbfabf375.pth',
  'd910d855fd179dc066c1a8ee69277898.pth',
  'dc9247034a68285efea8a3df5e20f054.pth',
  'dd686080a4d1cac8e85013a1e4383bdd.pth',
  'de71aa5eca9ee76a95f577622f465c85.pth',
  'e23f62bb4794ee6a7fdd0518ed16e820.pth',
  'adace8a468fd575037939c05190e283f.pth',
  'af4ff1c4a94383e9ca017e2245ec1dae.pth',
  'b00152d19e8f2b87b2d2b5b947dc0b8d.pth',
  'b1d75ad18d986ec760005b40a079e2d3.pth',
  'b1e5b106e6e25c44a4530e3038c81e85.pth',
  '78d707f4d87b5bfd730ff85f0d8004ee.pth',
  '7a82a497bc4d10511d385f351a1d14c5.pth',
  '807ef57d3d9d13eeccf25325b962dc82.pth',
  '70172e6afe6aff7847f90c1ac631b97f.pth',
  '72a9f3c57e40416f8884a069d9619eaf.pth',
  'be102516d65bcf23ff59f7e635b49cca.pth',
  'be16ada66829940a451786f3cbfd6769.pth',
  'bf73707d87715aa8ad5067eac75a07f7.pth',
  'bfe7d0102dcd0deff43af5716b936459.pth',
  'c1ebc4254a9f43823c0d2e0152e91b5.pth',
  'c3bc0cd2648e76b9187964c89b3399f1.pth',
  '8b7933b0376cea4a1efe98244cb8c300.pth',
  '8d861e4406a9d3258534bca5562e21be.pth',
  '8e20da9c3f63ac2ce902acf138e668e2.pth',
  '8ea8ced5529a3ffa7ae0a62f7ca532f1.pth',
  '8f2b8d281413a8bd5b326e4735ab9003.pth',
  '91235f7d65aec958ca972daa503b3095.pth',
  '9dd18bbd88df283a6b36e3e6a5b248ba.pth',
  'a1858315e1b17f57e1507433bf0da3de.pth',
  'a1bc36109cd382b78340c8802f48c170.pth',
  '32bb26b4d2cd5ee0b3b14ef623ad866a.pth',
  '331601288075868e342fe691e18bb5fd.pth',
  '35ad544a3a4b25b122de9a89c84a71b7.pth',
  '365f8a3cf397adf66e71bbd43f7f5d20.pth',
  '368bbfbb2fe08a6b4c5c5c89015f1980.pth',
  '371b604f78300e02d76ab6ff59fe7e10.pth',
  '3a6fae97b5fa5cbb3db8babb13da5441.pth',
  'ac79fd7f10f274aba2c59a4d90e63212.pth',
  'c61edfb672986ee48a9393b5e735dbde.pth',
  'd30623112e58b893eee7d6dab02eb061.pth',
  '1ae823260851f7d9ea600d1a6d9f6e07.pth',
  '1b64b36bf7ddae3d7ad11050da24bb12.pth',
  '1ef68777bfdb7d6ba7a07ee616e34cd7.pth',
  '3f91158956ad7db0322747720d7d37e8.pth',
  '41ab1142420916e374bb1e92fd01dc00.pth',
  '4301fe10764677dcdf0266d76aa42ba.pth',
  '7f5db4889a433ce5e7a14f6d159dcd47.pth'
  ]

for fn in _fns:
  if fn in skip:
    continue
  _codes.append(torch.load(os.path.join(code_path, fn)).squeeze().float().cuda())
  _meshes.append(trimesh.load(os.path.join(mesh_path, fn[:-3] + 'ply')))

codes = torch.stack(_codes, 0)

def get_obj_code_random(batch_size, code_length=256):
  # code = torch.normal(mean=0, std=0.1, size=[batch_size, code_length]).float().cuda()
  idx = torch.randint(0, len(codes), size=[batch_size], device='cuda')
  return codes[idx], idx

def get_obj_mesh(idx) -> trimesh.Trimesh:
  return _meshes[idx]

def get_obj_mesh_by_code(code) -> trimesh.Trimesh:
  for i, c in enumerate(codes):
    if torch.norm(code - c) < 1e-8:
      return _meshes[i]

def get_grasp_code_random(batch_size, code_length):
  code = torch.normal(mean=0, std=1, size=[batch_size, code_length], device='cuda').float()
  return code


# Klein's bottle: c5032e4be091aabb36fe7a88df793982.pth

